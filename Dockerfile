# XiCON Dance SCAIL - RunPod Serverless
# This Dockerfile builds a containerized ComfyUI worker with WanVideo SCAIL for dance video generation
# For RunPod Serverless deployment

# clean base image containing only comfyui, comfy-cli and comfyui-manager
FROM runpod/worker-comfyui:5.5.1-base

# CUDA Configuration for RunPod
ENV CUDA_VISIBLE_DEVICES=0
ENV PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
ENV CUDA_LAUNCH_BLOCKING=0

# install custom nodes into comfyui (first node with --mode remote to fetch updated cache)
# The workflow's custom nodes are listed under an unknown registry and no GitHub repo (aux_id) was provided,
# so they cannot be automatically installed. Skipping installation and listing the unresolved nodes below:
# Could not resolve unknown registry node: WanVideoModelLoader (no aux_id provided)
# Could not resolve unknown registry node: WanVideoDecode (no aux_id provided)
# Could not resolve unknown registry node: WanVideoVAELoader (no aux_id provided)
# Could not resolve unknown registry node: WanVideoBlockSwap (no aux_id provided)
# Could not resolve unknown registry node: WanVideoLoraSelect (no aux_id provided)
# Could not resolve unknown registry node: WanVideoSetLoRAs (no aux_id provided)
# Could not resolve unknown registry node: WanVideoSetBlockSwap (no aux_id provided)
# Could not resolve unknown registry node: WanVideoEmptyEmbeds (no aux_id provided)
# Could not resolve unknown registry node: ImageResizeKJv2 (no aux_id provided)
# Could not resolve unknown registry node: VHS_LoadVideo (no aux_id provided)
# Could not resolve unknown registry node: VHS_VideoCombine (no aux_id provided)
# Could not resolve unknown registry node: INTConstant (no aux_id provided)
# Could not resolve unknown registry node: FloatConstant (no aux_id provided)
# Could not resolve unknown registry node: GetImageSizeAndCount (no aux_id provided)
# Could not resolve unknown registry node: WanVideoAddSCAILPoseEmbeds (no aux_id provided)
# Could not resolve unknown registry node: CLIPVisionLoader (no aux_id provided)
# Could not resolve unknown registry node: WanVideoClipVisionEncode (no aux_id provided)
# Could not resolve unknown registry node: NLFPredict (no aux_id provided)
# Could not resolve unknown registry node: DownloadAndLoadNLFModel (no aux_id provided)
# Could not resolve unknown registry node: WanVideoSamplerv2 (no aux_id provided)
# Could not resolve unknown registry node: WanVideoSchedulerv2 (no aux_id provided)
# Could not resolve unknown registry node: WanVideoAddSCAILReferenceEmbeds (no aux_id provided)
# Could not resolve unknown registry node: WanVideoSamplerExtraArgs (no aux_id provided)
# Could not resolve unknown registry node: WanVideoContextOptions (no aux_id provided)
# Could not resolve unknown registry node: RenderNLFPoses (no aux_id provided)
# Could not resolve unknown registry node: PoseDetectionVitPoseToDWPose (no aux_id provided)
# Could not resolve unknown registry node: OnnxDetectionModelLoader (no aux_id provided)
# Could not resolve unknown registry node: WanVideoTextEncodeCached (no aux_id provided)
# Could not resolve unknown registry node: SimpleCalculatorKJ (no aux_id provided)

# download models into comfyui
RUN comfy model download --url https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/blob/main/SCAIL/Wan21-14B-SCAIL-preview_fp8_e4m3fn_scaled_KJ.safetensors --relative-path models/diffusion_models --filename Wan21-14B-SCAIL-preview_fp8_e4m3fn_scaled_KJ.safetensors
RUN comfy model download --url https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors --relative-path models/clip --filename clip_vision_h.safetensors
RUN comfy model download --url https://github.com/isarandi/nlf/releases/download/v0.3.2/nlf_l_multi_0.3.2.torchscript --relative-path models/checkpoints --filename nlf_l_multi_0.3.2.torchscript

# Download missing models
# VAE Model (508 MB)
RUN comfy model download --url https://huggingface.co/Wan-AI/Wan2.1-T2V-14B/resolve/main/Wan2.1_VAE.pth --relative-path models/vae --filename Wan2.1_VAE.pth

# Text Encoder (11.4 GB)
RUN comfy model download --url https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5-xxl-enc-bf16.safetensors --relative-path models/text_encoders --filename umt5-xxl-enc-bf16.safetensors

# LightX2V LoRA (739 MB)
RUN comfy model download --url https://huggingface.co/lightx2v/Wan2.1-I2V-14B-480P-StepDistill-CfgDistill-Lightx2v/resolve/main/loras/Wan21_I2V_14B_lightx2v_cfg_step_distill_lora_rank64.safetensors --relative-path models/loras --filename lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors

# ViTPose ONNX Model
RUN comfy model download --url https://huggingface.co/Kijai/vitpose_comfy/resolve/main/onnx/vitpose_h_wholebody_model.onnx --relative-path models/detection --filename vitpose_h_wholebody_model.onnx

# ViTPose Data Binary (required alongside .onnx)
RUN comfy model download --url https://huggingface.co/Kijai/vitpose_comfy/resolve/main/onnx/vitpose_h_wholebody_data.bin --relative-path models/detection --filename vitpose_h_wholebody_data.bin

# YOLOv10m ONNX
RUN comfy model download --url https://huggingface.co/Wan-AI/Wan2.2-Animate-14B/resolve/main/process_checkpoint/det/yolov10m.onnx --relative-path models/detection --filename yolov10m.onnx

# Install custom nodes
# WanVideo Wrapper (includes WanVideo*, SCAIL*, NLF* nodes)
RUN cd /comfyui/custom_nodes && \
    git clone https://github.com/kijai/ComfyUI-WanVideoWrapper.git && \
    cd ComfyUI-WanVideoWrapper && \
    pip install -r requirements.txt

# SCAIL Pose (RenderNLFPoses, PoseDetection nodes)
RUN cd /comfyui/custom_nodes && \
    git clone https://github.com/kijai/ComfyUI-SCAIL-Pose.git && \
    cd ComfyUI-SCAIL-Pose && \
    pip install -r requirements.txt

# KJ Nodes (ImageResizeKJv2, SimpleCalculatorKJ)
RUN cd /comfyui/custom_nodes && \
    git clone https://github.com/kijai/ComfyUI-KJNodes.git && \
    cd ComfyUI-KJNodes && \
    pip install -r requirements.txt

# Video Helper Suite (VHS_LoadVideo, VHS_VideoCombine)
RUN cd /comfyui/custom_nodes && \
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git && \
    cd ComfyUI-VideoHelperSuite && \
    pip install -r requirements.txt

# Configure detection model paths for SCAIL-Pose
RUN mkdir -p /comfyui/models/detection && \
    echo "scail_pose:" > /comfyui/extra_model_paths.yaml && \
    echo "  base_path: /comfyui/models/" >> /comfyui/extra_model_paths.yaml && \
    echo "  detection: detection/" >> /comfyui/extra_model_paths.yaml

# Copy custom handler and dependencies
COPY XiCON/XiCON_Dance_SCAIL/handler.py /handler.py
COPY XiCON/XiCON_Dance_SCAIL/request_transformer.py /request_transformer.py
COPY XiCON/XiCON_Dance_SCAIL/workflow_template.json /workflow_template.json
COPY XiCON/XiCON_Dance_SCAIL/gpu_validator.py /gpu_validator.py
COPY XiCON/XiCON_Dance_SCAIL/start.sh /start.sh

# Make scripts executable
RUN chmod +x /start.sh /gpu_validator.py

# Use custom start script with GPU validation
CMD ["/start.sh"]
