# PenaltyIQ ⚽🤖
**AI-Powered Biomechanical Motion Analysis Platform**

[![Flutter](https://img.shields.io/badge/Frontend-Flutter-02569B?logo=flutter)](https://flutter.dev/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![MediaPipe](https://img.shields.io/badge/AI-MediaPipe-orange)](https://developers.google.com/mediapipe)
[![NumPy](https://img.shields.io/badge/Math-NumPy-013243?logo=numpy)](https://numpy.org/)

## 📌 Executive Summary
PenaltyIQ is a full-stack Biomedical Engineering application that brings clinical-grade motion analysis to standard smartphones. By leveraging advanced Computer Vision and an Inverse Kinematics (IK) rule-based engine, the system analyzes football (soccer) penalty kicks. 

It extracts precise joint kinematics from video, computes complex biomechanical variables, and generates actionable, scientific-grade coaching feedback aimed at improving athletic performance and mitigating injury risks.

## ✨ Key Technical Achievements
*   **Markerless Motion Capture:** Utilizes Google MediaPipe Pose to extract 33 skeletal landmarks reliably without any physical wearable sensors.
*   **Kinematic Signal Processing:** Computes critical joint angles (Trunk Inclination, Hip Flexion, Knee Flexion) using dot-product vector mathematics, smoothed by an adaptive Savitzky-Golay filter to eliminate motion blur and tracking noise.
*   **Automated Event Detection:** Intelligently pinpoints the "Backswing" and "Ball Contact" frames based on local minima/maxima of joint angle time-series.
*   **Biomechanical Scoring Engine:** A robust, rule-based Inverse Kinematics (IK) engine that maps dynamic player kinematics against professional empirical priors (based on Arguz 2021) to generate a technique score out of 100.
*   **Cross-Platform UI:** A highly responsive Flutter frontend allowing athletes to record videos, view 2D skeleton overlays, and read feedback seamlessly.

## 🏗️ System Architecture
The repository uses a separated client-server architecture:
*   **Frontend (`penaltyiq-flutter/`):** Built with Flutter (Dart), handling video capture, local state management, and high-performance UI rendering.
*   **Backend (`penaltyiq-backend/`):** Built with Python and FastAPI. It houses the heavyweight AI processing pipeline to avoid deploying 200MB+ models onto mobile devices.
*   **Scientific Core:** OpenCV (`cv2`) for frame-by-frame extraction, MediaPipe for pose detection, and NumPy/SciPy for biomechanical mathematics.

For a deeper dive into the system design, see the documentation:
- [System Architecture](docs/architecture.md)
- [Biomechanical AI Pipeline](docs/pipeline.md)
- [REST API Specs](docs/api.md)

## 🚀 How to Run Locally

### Prerequisites
*   Python 3.10+
*   Flutter SDK

### 1. Start the AI Backend
```bash
cd penaltyiq-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 2. Start the Mobile Frontend
```bash
cd penaltyiq-flutter
flutter pub get
flutter run
```
## 📸 App Screenshots

### 🏠 Home / Main Interface
![Home Screen](assets/screenshots/Screenshot%202026-06-08%20203426.png)

### 📤 Upload & Video Analysis
![Upload Screen](assets/screenshots/Screenshot%202026-06-08%20203446.png)

### 🧠 Biomechanical Feedback Output
![Feedback Screen](assets/screenshots/Screenshot%202026-06-08%20203502.png)

### 📊 Score Breakdown View
![Score Screen](assets/screenshots/Screenshot%202026-06-08%20203523.png)

### 📱 Mobile UI 
![Demo 1](assets/screenshots/WhatsApp%20Image%202026-06-08%20at%208.31.50%20PM%20(1).jpeg)

### 📱 Mobile UI
![Demo 2](assets/screenshots/WhatsApp%20Image%202026-06-08%20at%208.31.50%20PM.jpeg)

## 🔮 Roadmap & Future Improvements
*   **3D Pose Estimation:** Transitioning from 2D coordinate extraction to 3D depth reconstruction to eliminate foreshortening (depth loss) on non-sagittal camera angles.
*   **ML-Based Scoring:** Augmenting the rule-based IK engine with a custom-trained machine learning model for adaptive, data-driven technique scoring.
*   **Real-time Inference:** Optimizing the computer vision pipeline to provide live biomechanical feedback using WebRTC or on-device edge AI.

## 👨‍💻 Developer & Engineer
**Built by a Biomedical and Software Engineer passionate about sports tech, human movement analysis, and AI.**
