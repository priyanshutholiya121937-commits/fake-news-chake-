document.addEventListener('DOMContentLoaded', () => {
  // Tab Switching
  const tabCamera = document.getElementById('tab-camera-btn');
  const tabUpload = document.getElementById('tab-upload-btn');
  const contentCamera = document.getElementById('camera-tab-content');
  const contentUpload = document.getElementById('upload-tab-content');


  if (tabCamera && tabUpload) {
    tabCamera.addEventListener('click', () => {
      tabCamera.classList.add('active');
      tabUpload.classList.remove('active');
      contentCamera.classList.add('active');
      contentUpload.classList.remove('active');
      startCamera();
    });

    tabUpload.addEventListener('click', () => {
      tabUpload.classList.add('active');
      tabCamera.classList.remove('active');
      contentUpload.classList.add('active');
      contentCamera.classList.remove('active');
      stopCamera();
    });
  }

  // Camera Management
  const video = document.getElementById('camera-video');
  const previewImg = document.getElementById('captured-preview');
  const captureBtn = document.getElementById('capture-btn');
  const retakeBtn = document.getElementById('retake-btn');
  const analyzeCameraBtn = document.getElementById('analyze-camera-btn');
  const cameraDataInput = document.getElementById('camera-image-data');
  const cameraErrorMsg = document.getElementById('camera-error-message');

  let mediaStream = null;

  async function startCamera() {
    if (!video) return;
    if (cameraErrorMsg) cameraErrorMsg.style.display = 'none';

    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        mediaStream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: { ideal: "environment" },
            width: { ideal: 1280 },
            height: { ideal: 720 }
          }
        });
        video.srcObject = mediaStream;
        await video.play();
        if (captureBtn) captureBtn.disabled = false;
      } else {
        showCameraError("Camera access is not supported by your browser or requires a secure HTTPS/localhost context.");
      }
    } catch (err) {
      console.warn("Camera init error:", err);
      let msg = "Could not access camera. Please allow camera permissions or upload an image file.";
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        msg = "Camera permission was denied. Please allow camera access in your browser settings.";
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        msg = "No camera hardware detected on this device.";
      }
      showCameraError(msg);
    }
  }

  function stopCamera() {
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop());
      mediaStream = null;
    }
  }

  function showCameraError(msg) {
    if (cameraErrorMsg) {
      cameraErrorMsg.textContent = msg;
      cameraErrorMsg.style.display = 'block';
    }
  }

  // Capture Snapshot
  if (captureBtn) {
    captureBtn.addEventListener('click', () => {
      if (!video || !video.videoWidth) return;

      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
      if (cameraDataInput) cameraDataInput.value = dataUrl;

      if (previewImg) {
        previewImg.src = dataUrl;
        previewImg.removeAttribute('hidden');
      }
      video.style.display = 'none';

      captureBtn.style.display = 'none';
      if (retakeBtn) retakeBtn.style.display = 'inline-flex';
      if (analyzeCameraBtn) analyzeCameraBtn.disabled = false;
    });
  }

  // Retake Snapshot
  if (retakeBtn) {
    retakeBtn.addEventListener('click', () => {
      if (cameraDataInput) cameraDataInput.value = '';
      if (previewImg) {
        previewImg.setAttribute('hidden', '');
      }
      if (video) video.style.display = 'block';

      if (captureBtn) captureBtn.style.display = 'inline-flex';
      retakeBtn.style.display = 'none';
      if (analyzeCameraBtn) analyzeCameraBtn.disabled = true;
    });
  }

  // Auto-start camera if camera tab is active
  if (contentCamera && contentCamera.classList.contains('active')) {
    startCamera();
  }

  // Cleanup camera stream on unload
  window.addEventListener('beforeunload', stopCamera);

  // Drag & Drop Image Upload Handler
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('image-file-input');
  const uploadPreviewContainer = document.getElementById('upload-preview-container');
  const uploadPreviewImg = document.getElementById('upload-preview-img');
  const uploadFilename = document.getElementById('upload-filename');
  const uploadClearBtn = document.getElementById('upload-clear-btn');
  const analyzeUploadBtn = document.getElementById('analyze-upload-btn');

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        handleFileSelection(fileInput.files[0]);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files.length > 0) {
        handleFileSelection(fileInput.files[0]);
      }
    });
  }

  function handleFileSelection(file) {
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      alert("File exceeds maximum allowed size of 5 MB.");
      if (fileInput) fileInput.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
      if (uploadPreviewImg) uploadPreviewImg.src = e.target.result;
      if (uploadFilename) uploadFilename.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      if (uploadPreviewContainer) uploadPreviewContainer.style.display = 'block';
      if (dropzone) dropzone.style.display = 'none';
      if (analyzeUploadBtn) analyzeUploadBtn.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  if (uploadClearBtn) {
    uploadClearBtn.addEventListener('click', () => {
      if (fileInput) fileInput.value = '';
      if (uploadPreviewContainer) uploadPreviewContainer.style.display = 'none';
      if (dropzone) dropzone.style.display = 'block';
      if (analyzeUploadBtn) analyzeUploadBtn.disabled = true;
    });
  }
});
