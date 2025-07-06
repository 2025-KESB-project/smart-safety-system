# smart-safety-system
Conveyor AI Safety System
# 📦 프로젝트명: 28일 후 – AI 기반 스마트 안전 컨베이어 시스템

## 📌 개요
작업자 안전을 위해 YOLO, OpenPose 기반의 실시간 위험 감지 시스템을 개발합니다.  
정형·비정형 작업 구분 및 Safe 모드 제공으로 끼임 사고, 안전 미준수 등의 사고를 최소화합니다.

## 🧠 주요 기능
- YOLO 기반 객체 인식 (사람, 손, 얼굴 등)
- OpenPose 기반 자세 분석 및 이상 감지
- 위험 감지 시 알림 / 전원 차단
- 제스처 인식 기반 정지
- Safe 모드/정형/비정형 모드 전환 제어

## ⚙️ 기술 스택
| 구분       | 내용                            |
|------------|---------------------------------|
| Language   | Python, JavaScript              |
| Framework  | FastAPI, Flask (Backend), React (Frontend) |
| AI Model   | YOLOv5, OpenPose                |
| DB         | SQLite 또는 Firebase            |
| Deployment | Raspberry Pi, Local PC          |

## 🏗️ 프로젝트 구조
```bash
.
├── backend/
├── frontend/
├── ai-models/
├── hardware/
├── data/
└── README.md