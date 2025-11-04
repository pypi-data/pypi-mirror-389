import torch
from tqdm import tqdm
from vigorvision.nn.loss import ComputeLoss
from vigorvision.utils.metrics import DetectionMetrics
from vigorvision.utils.general import increment_path, colorstr
from vigorvision.utils.decoder import PredictionDecoder
from vigorvision.utils.iou import nms as non_max_suppression


class Validator:
    def __init__(
        self,
        model,
        dataloader,
        device,
        anchors,
        num_classes,
        use_amp=True,
        conf_thres=0.25,
        iou_thres=0.6,
        max_det=100,
        save_dir=None,
        verbose=False,
    ):
        """
        Validator for evaluating model on val/test set.
        """
        self.model = model.to(device).eval()
        self.device = device
        self.dataloader = dataloader
        self.use_amp = use_amp
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self.max_det = max_det
        self.anchors = anchors
        self.num_classes = num_classes
        self.loss_fn = ComputeLoss(anchors=anchors, num_classes=num_classes, device=device)
        self.metrics = DetectionMetrics(num_classes=num_classes)
        self.save_dir = save_dir
        self.verbose = verbose
        self.pred_decoder = PredictionDecoder(
            conf_threshold=conf_thres,
            iou_threshold=iou_thres,
            max_detections=max_det,
            agnostic=False  # or True if you want class-agnostic NMS
        )
        # prefer model-provided strides; fall back to provided strides if any
        self.strides = getattr(model, "stride", None) or getattr(model, "strides", None)
    @torch.no_grad()
    def evaluate(self):
        """
        Run validation for one full epoch.
        Returns:
            Dictionary of validation statistics
        """
        self.model.eval()
        self.metrics.reset()

        total_loss = torch.zeros(4, device=self.device)

        pbar = tqdm(self.dataloader, desc="Validating", leave=False)

        for batch in pbar:
            imgs, targets = batch
            imgs = imgs.to(self.device)

            # `targets` from the dataloader is a sequence (one tensor per sample).
            # Build a concatenated target tensor of shape (n,6): [img_idx, cls, x, y, w, h]
            tgt_list = []
            for i, t in enumerate(targets):
                if isinstance(t, torch.Tensor) and t.numel():
                    t = t.to(self.device)
                    img_idx = torch.full((t.shape[0], 1), i, device=self.device, dtype=t.dtype)
                    tgt_list.append(torch.cat([img_idx, t], dim=1))

            if len(tgt_list):
                targets_tensor = torch.cat(tgt_list, dim=0)
            else:
                targets_tensor = torch.zeros((0, 6), device=self.device)

            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=self.use_amp):
                preds = self.model(imgs)

                # Attempt to compute loss only when preds are raw network outputs (list of scale tensors)
                try:
                    if isinstance(preds, (list, tuple)) and isinstance(preds[0], torch.Tensor) and preds[0].ndim >= 4:
                        loss_items = self.loss_fn(preds, targets_tensor)
                        # loss_items may be (loss, box, cls, obj) or (loss, {'box_loss':..., ...})
                        if isinstance(loss_items, tuple) or isinstance(loss_items, list):
                            loss, box_loss, cls_loss, obj_loss = loss_items
                        elif isinstance(loss_items, dict):
                            loss = loss_items.get('total_loss', torch.tensor(0.0, device=self.device))
                            box_loss = loss_items.get('box_loss', torch.tensor(0.0, device=self.device))
                            cls_loss = loss_items.get('cls_loss', torch.tensor(0.0, device=self.device))
                            obj_loss = loss_items.get('obj_loss', torch.tensor(0.0, device=self.device))
                        else:
                            loss = box_loss = cls_loss = obj_loss = torch.tensor(0.0, device=self.device)

                        total_loss[0] += loss.item() if hasattr(loss, 'item') else float(loss)
                        total_loss[1] += box_loss.item() if hasattr(box_loss, 'item') else float(box_loss)
                        total_loss[2] += cls_loss.item() if hasattr(cls_loss, 'item') else float(cls_loss)
                        total_loss[3] += obj_loss.item() if hasattr(obj_loss, 'item') else float(obj_loss)
                except Exception:
                    # If loss computation fails for any reason, skip it but continue evaluation.
                    pass

            # Decode predictions into per-image detections (x1,y1,x2,y2,score,cls)
            decoded_preds = None
            try:
                if isinstance(preds, (list, tuple)) and isinstance(preds[0], torch.Tensor) and preds[0].ndim >= 4:
                    # raw network outputs per scale -> use decoder
                    decoded_preds = self.pred_decoder(preds, anchors=self.anchors, strides=self.strides, num_classes=self.num_classes)
                elif isinstance(preds, torch.Tensor) and preds.ndim == 3:
                    # Already-decoded tensor [bs, N, no] -> split per image
                    decoded_preds = [preds[i].detach().cpu() for i in range(preds.shape[0])]
                elif isinstance(preds, (list, tuple)) and all(isinstance(p, torch.Tensor) and p.ndim == 2 for p in preds):
                    # List of per-image tensors
                    decoded_preds = [p.detach().cpu() for p in preds]
                else:
                    # Last resort: try to move to CPU and interpret as list
                    try:
                        decoded_preds = [p.detach().cpu() for p in preds]
                    except Exception:
                        decoded_preds = [torch.zeros((0, 6)) for _ in range(imgs.size(0))]
            except Exception:
                decoded_preds = [torch.zeros((0, 6)) for _ in range(imgs.size(0))]

            # Update metrics per-sample, always using CPU tensors
            for i in range(imgs.size(0)):
                pred = decoded_preds[i] if i < len(decoded_preds) else torch.zeros((0, 6))
                if isinstance(pred, torch.Tensor):
                    pred_cpu = pred.detach().cpu()
                else:
                    pred_cpu = torch.tensor(pred)

                gt = targets[i]
                gt_cpu = gt.detach().cpu() if isinstance(gt, torch.Tensor) else torch.tensor([])

                # DetectionMetrics expects detections [N,6] and labels [M,5]
                self.metrics.update(preds=pred_cpu, targets=gt_cpu)

            # free GPU memory from this batch
            try:
                del preds, decoded_preds, targets_tensor
                torch.cuda.empty_cache()
            except Exception:
                pass

        # Aggregate metrics
        results = self.metrics.compute()
        mean_loss = total_loss / len(self.dataloader)

        val_stats = {
            "val/total_loss": mean_loss[0].item(),
            "val/box_loss": mean_loss[1].item(),
            "val/cls_loss": mean_loss[2].item(),
            "val/obj_loss": mean_loss[3].item(),
            "metrics/precision": results["precision"],
            "metrics/recall": results["recall"],
            "metrics/mAP_0.5": results["map_50"],
            "metrics/mAP_0.5:0.95": results["map_50_95"],
        }

        if self.verbose:
            print(colorstr("Validator Results:"))
            for k, v in val_stats.items():
                print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")

        return val_stats
