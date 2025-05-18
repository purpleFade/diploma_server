# Diploma_2025_Backend

This repository contains the backend service for microservice that analyzes and annotates tactical images.  
The service is built with **Python + Flask**, uses **OpenCV** for drawing annotations, and relies on the **Roboflow Inference SDK** to run the *military_objects/1* model hosted on Roboflow.

> **Live demo:** [Click here](https://diploma-server-xmh0.onrender.com)

---

## ✨ Key Features

| Area | Details |
|------|---------|
| **REST API** | `POST /process_image` accepts an image, returns JSON + public URLs to results. |
| **Roboflow integration** | Sends each upload to the hosted *military_objects/1* model and receives detections. |
| **Auto-annotation** | Draws bounding boxes + labels on the image with OpenCV. |
| **Rich metadata** | Saves a per-request `object_info.json` (ID, class, confidence, coordinates). |
| **Result hosting** | Annotated image and JSON are exposed via `GET /results/<file>` so the frontend can fetch or preview them. |
| **Docker-ready** | A basic `Dockerfile` can wrap the service for portable deployment. |

---

## 🛠️ Technology Stack

- **Python 3.10+**
- **Flask** – lightweight web framework  
- **OpenCV-Python** – image handling & drawing  
- **Roboflow Inference SDK** – cloud object-detection API  
- **Flask-CORS** – cross-origin requests for the frontend  
- **Docker** *(optional, deployment)*

---

## 🚀 Quick Start

1. **Clone the repo**

   ```bash
   git clone https://github.com/purpleFade/Practice_2024_backend.git
   cd Practice_2024_backend
   ```

2. **Create & activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your Roboflow API key**

   ```bash
   # macOS / Linux
   export ROBOFLOW_API_KEY="YOUR_KEY_HERE"

   # Windows (PowerShell)
   setx ROBOFLOW_API_KEY "YOUR_KEY_HERE"
   ```

   > You will find your key in the **Roboflow → Settings → API Key** panel.  
   > The service fails fast if the variable is missing.

5. **Run the server**

   ```bash
   python app.py
   ```

   The API is now available at **http://127.0.0.1:5000**.

---

## 📡 API Endpoints

| Method | Route | Body / Params | Description |
|--------|-------|---------------|-------------|
| **POST** | `/process_image` | *multipart/form-data* field **image** | Uploads an image, runs Roboflow detection, returns JSON and absolute URLs to the results. |
| **GET** | `/results/<path>` | — | Serves images or JSON that live under the `results/` directory. |

Successful `POST /process_image` response (truncated):

```json
{
  "message": "Image processed successfully with Roboflow.",
  "results_folder": "run_20250518_161530_a1b2c3",
  "annotated_image_url": "http://127.0.0.1:5000/results/run_.../yolo.jpg",
  "object_info_url": "http://127.0.0.1:5000/results/run_.../object_info.json",
  "object_info": [
    {
      "id": 0,
      "type": "tank",
      "confidence": 0.92,
      "coordinates": { "x": 34, "y": 58, "width": 220, "height": 130 }
    }
  ]
}
```

---

## 🗂️ Folder Structure

```
Practice_2024_backend/
├── app.py               # Main Flask application
├── utils/               # (Optional) utility helpers
├── results/             # Auto-created; holds per-request subfolders
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation (this file)
```

---

## 🐳 Docker (optional)

Build & run:

```bash
docker build -t diploma-backend .
docker run -d -p 5000:5000 -e ROBOFLOW_API_KEY=YOUR_KEY diploma-backend
```

---

## 🤝 Contributing

1. **Fork** the repo  
2. Create a **feature branch**  
   ```bash
   git checkout -b feature/my-idea
   ```
3. **Commit** your changes  
   ```bash
   git commit -m "Describe my idea"
   ```
4. **Push** to your fork and open a **pull request**

---

## 📝 License

Distributed under the **MIT License**. See the `LICENSE` file for details.
