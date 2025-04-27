// Initialize AOS
AOS.init();

// Loader functionality
window.addEventListener('load', () => {
  const loader = document.getElementById('loader');
  loader.style.opacity = '0';
  setTimeout(() => loader.style.display = 'none', 500);
});

// Form handling with progress bar
const form = document.getElementById('uploadForm');
const loading = document.getElementById('loading');
const progressBar = document.getElementById('progressBar');
const progressFill = document.getElementById('progressFill');
const analysisResult = document.getElementById('analysisResult');
const analysisText = document.getElementById('analysisText');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const fileInput = form.file;
  const formData = new FormData();
  formData.append('file', fileInput.files[0]);

  loading.classList.remove('hidden');
  progressBar.classList.remove('hidden');
  analysisResult.classList.add('hidden');

  try {
    // Simulate progress
    let progress = 0;
    const progressInterval = setInterval(() => {
      progress += 10;
      progressFill.style.width = `${progress}%`;
      if (progress >= 90) clearInterval(progressInterval);
    }, 200);

    // Step 1: Upload the file
    const uploadRes = await fetch('/upload', {
      method: 'POST',
      body: formData
    });
    const uploadData = await uploadRes.json();
    if (!uploadRes.ok) throw new Error(uploadData.error);

    // Step 2: Analyze the image
    const analyzeRes = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: uploadData.file_path })
    });
    const analyzeData = await analyzeRes.json();
    if (!analyzeRes.ok) throw new Error(analyzeData.error);

    clearInterval(progressInterval);
    progressFill.style.width = '100%';

    const analysis = analyzeData.analysis_results;
    analysisText.textContent = analysis.description || JSON.stringify(analysis, null, 2);
    analysisResult.classList.remove('hidden');
  } catch (err) {
    // Remove any existing error messages before appending the new one
    const existingError = document.querySelector('.alert-danger');
    if (existingError) existingError.remove();

    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger mt-4';
    errorDiv.textContent = `Error: ${err.message}`;
    form.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 3000);
  } finally {
    loading.classList.add('hidden');
    setTimeout(() => {
      progressBar.classList.add('hidden');
      progressFill.style.width = '0';
    }, 500);
  }
});
