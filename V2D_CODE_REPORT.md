# Video to Data (V2D) 코드 분석 보고서

> 대상 레포: `video_to_data/` (NVIDIA Isaac). 분석 기준 커밋: `8b37535c` (main).
> 이 문서는 코드의 문법이 아니라 **도커 이미지 · 패키지 · 클래스 · 함수 수준의 설계**를 설명한다.
> 세 단계 중 **Reconstruction**과 **Robotic Grounding**을 집중적으로 다루고, Video Ingestion은 개요 수준으로 정리한다.

---

## 목차

1. [전체 구조 한눈에 보기](#1-전체-구조-한눈에-보기)
2. [1단계: Video Ingestion Agent (개요)](#2-1단계-video-ingestion-agent-개요)
3. [2단계: Reconstruction](#3-2단계-reconstruction)
   - 3.1 설계 원칙: 호스트 오케스트레이션 + 컨테이너 추론
   - 3.2 공유 인프라 (`v2d_common`, `v2d_docker`, `v2d_mv`)
   - 3.3 모듈 패턴 (`docker/` ↔ `lib/`)
   - 3.4 멀티뷰 HOI 파이프라인 (`run_mv_hoi_reconstruction`)
   - 3.5 HOI 객체 재구성 파이프라인 (`v2d_hoi_object_reconstruction`)
   - 3.6 Egocentric 파이프라인
   - 3.7 `v2d_task_library_loader`: 3단계로 넘어가는 다리
4. [3단계: Robotic Grounding](#4-3단계-robotic-grounding)
   - 4.1 두 개의 도커 이미지와 오케스트레이터
   - 4.2 데이터셋 레지스트리와 리타게팅 (IK)
   - 4.3 모션 교환 포맷 `motion_v1`
   - 4.4 지지면 재구성과 URDF 생성
   - 4.5 Isaac Lab 태스크: Sharpa 플로팅 핸드
   - 4.6 Isaac Lab 태스크: G1 전신 (SONIC + RL 잔차)
   - 4.7 전신 플래너 (`g1_planner`)
   - 4.8 RL 진입점 (`train` / `eval` / `dummy_agent`)
   - 4.9 테스트와 데이터 품질 검사
5. [단계 간 데이터 계약 요약](#5-단계-간-데이터-계약-요약)
6. [종합 평가](#6-종합-평가)

---

## 1. 전체 구조 한눈에 보기

V2D는 사람의 시연 영상을 로봇 학습 데이터로 바꾸는 파이프라인이며, 서로 독립적으로 실행 가능한 세 패키지로 나뉜다. 각 단계는 결과물을 **파일로 디스크에 기록**하고, 다음 단계는 그 파일을 읽는다. 따라서 어느 경계에서든 멈추고, 검사하고, 캐시하고, 재조합할 수 있다.

```
[영상]
  │
  ▼  video_ingestion_agent/   (Python venv + vLLM 서버)
  │    LangGraph 워크플로: 세그먼트 → 검증/정제 → 엔티티 그래프 → SigLIP-2 임베딩
  │    산출물: graph.db + vector.db (SQLite), clips_final.jsonl
  ▼
  ▼  reconstruction/          (모듈별 Docker 이미지, 호스트는 얇은 래퍼)
  │    깊이 · 마스크 · 6-DoF 객체 포즈 · 텍스처 메시 · 사람 신체(MHR/SMPL) · 손(MANO)
  │    산출물: PNG/JSON/GLB/NPZ 파일들, 그리고 {dataset}_loaded Parquet
  ▼
  ▼  robotic_grounding/       (Isaac Lab 2.3 Docker)
       MANO → 로봇 손 IK 리타게팅 → 지지면 생성 → Isaac Lab 환경에서 RSL-RL PPO 학습
       산출물: {dataset}_processed Parquet, *.usda, 정책 체크포인트(.pt/.onnx)
```

| 패키지 | 역할 | 런타임 |
|---|---|---|
| `video_ingestion_agent/` | 영상 → 행동 세그먼트 + 엔티티 씬 그래프 + 프레임 임베딩. 자연어 검색 에이전트 포함 | Python venv + vLLM |
| `reconstruction/` | 영상 → 3D 데이터. 30여 개 컨테이너 모듈 + 이를 엮는 `v2d_pipelines` | 모듈별 Docker |
| `robotic_grounding/` | 3D 데이터 → 리타게팅 → RL 정책. Isaac Lab 확장 패키지 | Docker (Isaac Lab) |

레포 전반을 관통하는 세 가지 설계 철학 (`README.md` "Design philosophy"):

1. **호스트 오케스트레이션, 컨테이너 추론.** 호스트에는 CUDA도 PyTorch도 설치하지 않는다. 얇은 Python 래퍼가 `docker run`을 조립해 실행할 뿐이다.
2. **타입이 있는 계약.** 패키지 경계에서는 `np.ndarray`나 `trimesh.Trimesh`를 넘기지 않고 `v2d_common`의 dataclass(`DepthImage`, `CameraIntrinsics`, `Transform3d` 등)를 쓴다.
3. **파일 기반 데이터플로.** 모듈끼리 인메모리 객체가 아니라 폴더의 파일로 소통한다.

---

## 2. 1단계: Video Ingestion Agent (개요)

> 위치: `video_ingestion_agent/src/video_ingestion_agent/`

긴 시연 영상을 그대로 3D 재구성에 넣는 것은 비효율적이다. 이 단계의 목적은 영상을 **행동 단위 클립으로 잘라 색인**해서, 뒤 단계가 "머그를 집는 장면만" 골라 처리할 수 있게 하는 것이다. 전체가 **LangGraph 상태 그래프**로 구성된다.

### 2.1 인제스천 그래프

`ingestion/ingestion_graph.py::create_pipeline_graph()`가 설정 토글에 따라 그래프를 조립한다. 검증(critic)과 정제(refine) 루프는 선택 사항이다.

```python
# ingestion/ingestion_graph.py (발췌)
workflow = StateGraph(PipelineState)
workflow.add_node("segment", segmentation_node)
workflow.set_entry_point("segment")
if enable_verification:
    workflow.add_node("extract_temp", extract_temp_node)
    workflow.add_node("verify", verification_node)
    workflow.add_edge("segment", "extract_temp")
    workflow.add_edge("extract_temp", "verify")
    if enable_refinement:
        workflow.add_node("refine", refinement_node)
        workflow.add_conditional_edges("verify", should_refine,
                                       {"refine": "refine", "cleanup": "cleanup_temp"})
        workflow.add_edge("refine", "verify")
```

이어서 `entity_extract → frame_embed → entity_link → db_write → report` 가 직렬로 붙는다. 상태는 `state.py::PipelineState`(TypedDict) 하나에 모두 담긴다.

핵심 아이디어 세 가지:

- **청크 기반 VLM 세그먼테이션.** `segmentation/segmenter.py::HybridSegmenter`가 15초 창(1.5초 중첩)으로 영상을 훑으며 VLM(기본 Qwen3-VL-8B, vLLM 서빙)에 묻고, 중첩 구간 결과를 `ClipDeduplicator`로 합친다.
- **Critic 루프.** `segmentation/critic.py::Critic`이 각 클립을 다시 보고 경계 조정 또는 재주석을 요구할 수 있다(최대 3회).
- **두 DB의 교차 참조.** `vector.db`의 프레임 임베딩마다 `segment_id`를 심어 두어, 시각 유사도 검색 결과가 곧바로 `graph.db`의 행동 세그먼트 경계로 풀린다.

### 2.2 데이터베이스

둘 다 **SQLite**(WAL 모드)이다. 별도 그래프 DB나 벡터 DB 엔진을 쓰지 않는다.

| 파일 | 작성자 | 테이블 |
|---|---|---|
| `graph.db` | `entity_graph/database_writer.py::DatabaseWriter` | `video_metadata`, `entities`, `relationships`, `action_segments` |
| `vector.db` | `utils/vector_database.py::VectorDatabase` | `videos`, `frame_embeddings` (768-d SigLIP-2, pickled float32, `segment_id` 컬럼) |

벡터 검색은 코사인 유사도 전수 스캔이다(10만 프레임 규모까지는 충분하다고 문서가 명시).

### 2.3 검색 에이전트와 모델 백엔드

- `retrieval/retrieval_graph.py::RetrievalAgent`: `task_decomposer → (병렬 Send) task_search → vqa_synthesizer`. 도구는 `SearchGraphTool`(SQL), `SearchFramesTool`(SigLIP-2 텍스트 임베딩 → 코사인), `ExtractClipTool`(ffmpeg).
- `models/model_manager.py::ModelManager`: 싱글턴. `vllm` / `local` / `api` 세 백엔드를 같은 인터페이스로 감싸고, 세그먼터·critic·엔티티 추출기가 GPU에 올린 모델 하나를 공유하게 한다.

### 2.4 2단계로 넘어가는 다리: `reconstruction_interface/`

의도적으로 얇게 만들어진 브릿지다. `_common/ingestion_io.py`의 `IngestedSegment(segment_id, video_path, start_t, end_t, object_label, action_label)`를 `clips_final.jsonl` 또는 `graph.db`에서 읽고, `ego_e2e/run_ego_e2e.py`가 세그먼트별로 ffmpeg로 클립을 잘라 **reconstruction 패키지의 `run_v2d_ego_e2e.py`를 별도 venv의 서브프로세스로 호출**한다. 이때 인제스천이 뽑은 `object_label`이 그대로 Grounding DINO의 텍스트 프롬프트가 된다. 인제스천 venv에 v2d/Docker 의존성이 섞이지 않게 하려는 격리다.

---

## 3. 2단계: Reconstruction

> 위치: `reconstruction/modules/` (34개 모듈), `reconstruction/scripts/`, `reconstruction/workflows/`

### 3.1 설계 원칙: 호스트 오케스트레이션 + 컨테이너 추론

모든 모듈은 같은 골격을 갖는다.

```
v2d_<name>/
├── lib/        # 무거운 ML 코드. 컨테이너 안에서만 설치. python -m v2d.<name>.lib.<tool>
├── docker/     # 호스트에 pip install -e. ML 의존성 0. run_<tool>() 함수 + argparse CLI
│   ├── Dockerfile, build.py, _config.py (IMAGE_NAME, MODULES_DIR)
│   └── run_<tool>.py
└── assets/     # 테스트 입력
```

흐름: **호스트 Python → `run_*()` 호출 → `docker run` 생성 → 컨테이너가 `lib/` 실행 → 결과가 마운트된 볼륨에 기록.**

이 구조의 이점은 (1) 모듈마다 CUDA/PyTorch 버전을 독립적으로 고정할 수 있고, (2) 호스트에서 `from v2d.moge.docker.run_video_to_depth import run_video_to_depth`처럼 import 해서 **Python 코드로 파이프라인을 조합**할 수 있다는 점이다. `v2d_pipelines`가 바로 그렇게 만들어진 메타 패키지다.

### 3.2 공유 인프라

#### `v2d_common/datatypes.py`: 타입 계약

모든 모듈이 공유하는 dataclass들. 전부 `to_dict/from_dict` + `save(path)/load(path)`의 동일한 규약을 갖는다.

| 클래스 | 필드 | 비고 |
|---|---|---|
| `DepthImage` | `depth` (m, float) | uint16 PNG 인코딩/디코딩 |
| `CameraIntrinsics` | `fx, fy, cx, cy, width, height` | `to_matrix()` → 3×3 K |
| `Transform3d` | `rotation`(wxyz quat), `translation`, `scale` | `to_matrix()` → 4×4, `from_matrix()` |
| `BoundingBox`, `BoundingBox3d`, `Point` | 좌표 | |
| `Mask`, `Image` | ndarray | PIL 변환 |
| `Sam2Prompt(s)` | 프레임, 점, 라벨, 박스 | `prompts.json` 계약 |

가장 중요한 결정은 **깊이의 역깊이(inverse-depth) uint16 인코딩**이다. 모듈 사이의 깊이 전송 포맷이 이 하나로 통일된다.

```python
# v2d_common/datatypes.py (발췌)
def to_pil_image(self) -> PILImage.Image:
    # pixel = 65535 * (1 / (depth_m + 1)); 가까울수록 값이 크고, 무한대는 0
    inverse_depth = 65535.0 * (1.0 / (self.depth + 1.0))
    return PILImage.fromarray(inverse_depth.clip(0, 65535).astype(np.uint16), mode="I;16")

@staticmethod
def from_array(arr: np.ndarray) -> 'DepthImage':
    return DepthImage(depth=1.0 / (arr.astype(np.float32) / 65535.0) - 1.0)
```

`Transform3d.to_matrix()`는 SciPy 없이 쿼터니언을 직접 전개한다. SciPy가 없는 컨테이너에서도 포즈를 읽을 수 있게 하려는 배려다.

같은 패키지의 다른 파일:

- `video.py`: `FrameSource.from_path()` / `FrameWriter.from_path()`가 이미지 디렉터리·HDF5·mp4를 같은 인터페이스로 읽고 쓴다. `lib/` 코드가 입력 형식에 무관해지는 핵심 추상화.
- `result_bundle.py`: Ego 파이프라인의 최종 산출물 `result_dir/{result.npz, manifest.json, mesh.obj}`를 쓰는 `write_result_bundle()`과, GeoCalib 중력 방향으로 번들 전체를 회전시키는 `gravity_align_result_bundle()`.
- `broadcast.py`: CLI 경로 인자에 numpy 브로드캐스팅 의미론을 부여(`--input 'a/*.png' --output 'out/*.json'`).

#### `v2d_docker/container.py`: 범용 `docker run` 생성기

모든 `docker/run_*.py`가 결국 이 함수 하나를 호출한다. 특징은 **볼륨 마운트를 인자 딕셔너리에서 자동 유도**한다는 점이다. 호스트 디렉터리마다 마운트 하나를 만들고, 컨테이너 안 경로로 인자를 다시 써 준다.

```python
# v2d_docker/container.py (발췌)
def run_in_container(image, module, inputs, outputs, extra_args=None, dev=False,
                     modules_dir=None, gpus=False, env=None, extra_volumes=None):
    inputs  = {k: os.path.abspath(v) for k, v in inputs.items()  if v is not None}
    outputs = {k: os.path.abspath(v) for k, v in outputs.items() if v is not None}
    for path in outputs.values():
        os.makedirs(_base_dir(path), exist_ok=True)

    dir_to_mount = {}                       # 호스트 디렉터리 → /data/<첫 인자 이름>
    for arg_name, path in {**inputs, **outputs}.items():
        dir_to_mount.setdefault(_base_dir(path), f"/data/{arg_name}")

    cmd = ["docker", "run", "--rm"]
    if gpus: cmd += ["--runtime=nvidia", "--gpus", "all"]
    cmd += ["--user", f"{os.getuid()}:{os.getgid()}", "-e", "HOME=/tmp"]
    for host_dir, container_dir in dir_to_mount.items():
        cmd += ["-v", f"{host_dir}:{container_dir}"]
    if dev: cmd += ["-v", f"{modules_dir}:/workspace"]   # 재빌드 없이 코드 수정 반영
    cmd += [image, "python", "-m", module]
    for arg_name, path in {**inputs, **outputs}.items():  # 호스트 경로 → 컨테이너 경로
        cmd += [f"--{arg_name}", f"{dir_to_mount[_base_dir(path)]}/{os.path.relpath(path, _base_dir(path))}"]
    ...
    subprocess.run(cmd, check=True)
```

`extra_args`는 `None/False`면 생략, `True`면 플래그, 그 외는 `--name value`로 변환된다. `dev=True`면 `modules/`를 `/workspace`에 덧씌워 이미지 재빌드 없이 코드를 고칠 수 있다.

#### `v2d_mv/`: 멀티뷰 공통 유틸 (이미지 없음)

- `rig/rig.py::RigConfig`: 카메라 토폴로지의 중심. `rig/rigs/stereo-4.yaml`(8카메라, 4스테레오 쌍) 같은 리그 YAML을 읽고, EDEX 캘리브레이션을 붙여 `get_camera(cam_id)`, `get_stereo_pairs()` 등을 제공한다. 캘리브레이션 로딩은 포맷 디스패치 구조(현재는 EDEX만).
- `rig/params.py::CameraParam(resolution, D_model, D, K, P, R, T)`: `scale(factor)`로 해상도와 K/P를 함께 재조정.
- `rig/edex.py`: EDEX 캘리브레이션 컨테이너의 pydantic 모델.
- `math/numpy_fn.py`: 투영/역투영, SE(3) 평균·RANSAC, 그리고 FoundationPose 출력 스무딩에 쓰이는 `pose_two_euro_filter` 등. `math/torch_fn.py`는 torch 미러.

### 3.3 모듈 패턴: `v2d_moge`와 `v2d_foundation_pose`

**호스트 래퍼**는 인자 정리만 한다. `run_*()` 함수와 `__main__`의 argparse가 1:1로 대응해야 한다는 규칙이 `CLAUDE.md`에 "wrapper completeness"로 명시되어 있다.

```python
# v2d_moge/docker/run_video_to_depth.py (발췌)
def run_video_to_depth(video_path, depth_folder, intrinsics_folder, weights_path,
                       batch_size=8, input_intrinsics_path=None, ..., dev=False) -> None:
    inputs  = {"video_path": video_path, "weights_path": weights_path}
    outputs = {"depth_folder": depth_folder, "intrinsics_folder": intrinsics_folder}
    ...
    run_in_container(image=IMAGE_NAME, module="v2d.moge.lib.video_to_depth",
                     inputs=inputs, outputs=outputs, extra_args={"batch_size": batch_size},
                     dev=dev, modules_dir=MODULES_DIR, gpus=True)
```

**Dockerfile**은 빌드 컨텍스트가 `modules/` 전체라는 점이 핵심이다. 그래서 `COPY . /workspace` 후 `pip install -e /workspace/v2d_common -e /workspace/v2d_moge/lib`처럼 형제 패키지를 함께 설치할 수 있다. MoGe는 13줄이면 끝나지만, FoundationPose는 pybind11·Eigen·kaolin·pytorch3d·nvdiffrast를 `TORCH_CUDA_ARCH_LIST="8.0 8.6 8.9 9.0"`로 빌드하며, 네이티브 확장 소스를 먼저 복사해 컴파일하고 그 다음에 나머지 소스를 복사해 **비싼 레이어 캐시가 소스 수정으로 깨지지 않게** 한다.

**컨테이너 진입점(`lib/`)**은 데이터 흐름을 이름에 담은 함수 하나(`video_to_depth`)와 같은 인자의 `__main__`으로 이루어진다. 모델은 모듈 전역에 지연 로딩·캐시된다.

#### 멀티뷰 프로그램의 OmegaConf 패턴

`lib/mv_<x>.py`는 항상 같은 이름의 `mv_<x>.yaml`과 짝을 이룬다. YAML은 리그 선택(`rig_config: stereo-4`, `cameras: [0,2,4,6]`), 필수 입력(`???`), 경로 템플릿(`"${depth_dir}/{cam_name}/depth"`: OmegaConf 보간 + `str.format` 카메라 확장)을 담는다. 설정을 아는 유일한 함수가 `*_from_config(cfg)`다.

```python
# v2d_foundation_pose/lib/mv_videos_to_poses.py — mv_videos_to_poses_from_config (요약)
rig = RigConfig(cfg.rig_config, camera_params_path=cfg.camera_params_path)
for cam_id in cfg.cameras:
    cam = rig.get_camera(cam_id)
    cam_intrinsics.append(cam.param.K); cam_extrinsics.append(cam.param.T)
    rgb_paths.append(Path(cfg.rgb_path_template.format(cam_name=cam.name)))
    depth_dirs.append(Path(cfg.depth_path_template.format(cam_name=cam.name)))
mv_videos_to_poses(cam_names=..., cam_intrinsics=..., ...)   # 설정을 모르는 순수 함수
```

`mv_videos_to_poses()` 본체는 `MultiViewTracker`(뷰 간 FoundationPose 가중치 공유, 가시 비율 가중 SE(3) 융합)로 0프레임에 `register()`, 이후 `track()`을 하고, `pose_two_euro_filter`로 스무딩해 `poses.npy` `(N,4,4)`를 쓴다.

### 3.4 멀티뷰 HOI 파이프라인: `v2d_pipelines/run_mv_hoi_reconstruction.py`

rosbag 하나에서 **객체 메시 포즈 + 사람 신체 파라미터**를 동시에 뽑는 대표 파이프라인이다. 15개의 docker 레이어 `run_*` 함수를 순서대로 호출하는 직선형 `main()`이며, 단계 결과는 `output_dir` 아래 고정 하위 폴더에 쌓인다.

```
                                     ┌─ Grounding DINO → SAM2(객체) → FoundationPose(MV) ─┐
rosbag → rosbag_to_edex → mv_preprocess → FoundationStereo ─┤                                                       ├─ chamfer 평가 · HOI 오버레이 · Wis3D
                                     └─ Detectron2(사람) → SAM2(사람) → SAM3D-Body(MHR) → SOMA 내보내기 ─┘
```

단계별 역할:

| 순서 | 함수 | 역할 |
|---|---|---|
| 1 | `run_rosbag_to_edex` | ROS bag → 카메라별 이미지 + EDEX 내부 파라미터 |
| 2 | `run_mv_preprocess` | 스테레오 정류, 리스케일, 비디오 인코딩, HOI bbox 재매핑, `prompt.txt` 추출, 외부 캘리브레이션 병합, 객체 메시 정렬 |
| 3 | `run_mv_image_list_to_depth` | FoundationStereo로 스테레오 쌍별 깊이 |
| 4-6 | DINO → SAM2 → `run_mv_videos_to_poses` | 객체 브랜치. 텍스트 프롬프트로 검출 → 마스크 → 6-DoF 추적 |
| 7-10 | Detectron2 → SAM2 → `run_mv_optimize_mhr_params` → `run_export_soma` | 사람 브랜치. 사람 검출/추적 → 마스크 → 멀티뷰 신체 파라미터 최적화 |
| 11-16 | postprocess | 융합 포인트클라우드, 지면 추정, chamfer 거리(객체/사람), 오버레이 영상, Wis3D 시각화 |

한 단계의 출력 디렉터리가 다음 단계의 입력이 되는 방식은 다음 발췌에서 그대로 보인다.

```python
# v2d_pipelines/run_mv_hoi_reconstruction.py (발췌)
run_mv_videos_to_poses(
    camera_params_path=os.path.join(preprocess_dir, "edex"),
    rgb_dir=preprocess_images_dir,
    depth_dir=foundation_stereo_dir,
    mask_dir=sam2_object_dir,
    mesh_path=_find_pinned_mesh(preprocess_mesh_dir),   # output_aligned.glb 존재 확인
    symmetry_path=sym_json if os.path.exists(sym_json) else None,
    weights_dir=os.path.join(RECON_DIR, "data/weights/foundation_pose"),
    output_dir=foundation_pose_dir,
    dev=dev,
)
```

이 파이프라인에는 **재시작/캐시 로직이 없다.** 반면 다음에 볼 HOI 객체 재구성과 Ego 파이프라인은 있다. 짝이 되는 `run_mv_calibration.py`는 체스보드 bag → `run_calibrate_extrinsics`(PnP 초기화 → Ceres 번들 조정) 두 단계로 외부 파라미터를 만들고, 그 결과 경로가 위 파이프라인의 `--extrinsics_camera_params_path`로 들어간다.

### 3.5 HOI 객체 재구성: `v2d_hoi_object_reconstruction`

손으로 객체를 돌리며 찍은 스테레오 영상에서 **6면이 모두 닫힌 텍스처 메시**를 만드는 파이프라인이다. 호스트 오케스트레이터 `docker/run_reconstruction.py`(약 1100줄) 하나가 **7개 이미지**(`v2d_hoi_object_reconstruction`, `v2d_cusfm`, `v2d_bundlesdf`, `v2d_foundation_stereo`, `v2d_sam2`, `v2d_foundation_pose`, `v2d_sam3d`)를 지휘한다.

**입력 계약**: `mapping_data_dir/{frames_meta.json, front_stereo_camera_left/*.jpeg, front_stereo_camera_right/*.jpeg}`. PyCuSFM의 `KeyframesMetadataCollection`을 단일 스테레오 쌍으로 좁힌 프로필이며, `schemas/frames_meta.schema.json`으로 검증한다.

#### BundleSDF 모드의 2단계 스캔 아이디어

객체를 세워 둔 채 한 바퀴(Stage 1) 돌고, 객체를 90° 눕혀 다시 한 바퀴(Stage 2) 돈다. Stage 1만으로는 바닥면이 비어 있는 메시가 나온다. 이 메시를 FoundationPose로 회전 구간을 가로질러 추적하면 Stage 2 키프레임의 카메라 포즈를 **Stage 1 객체 좌표계로 재표현**할 수 있고, 두 스테이지의 키프레임을 합쳐 두 번째 NeRF를 돌리면 바닥이 닫힌다.

```
준비(좌/우/캘리브레이션/비디오) → CuSFM(카메라 포즈) → 스캔 품질 게이트 → Stage-1 경계 자동 검출
  → Grounding DINO → [FoundationStereo 깊이 ∥ SAM2 마스크(+후처리)]
  → Stage-1 recon 셋업 → Stage-1 BundleSDF NeRF → 메시 중심화
  → FoundationPose 추적 → 월드 포즈 계산 + 스테이지 병합 → 병합 recon 셋업
  → 최종 BundleSDF NeRF → merged_recon/output.glb → 최종 FP 추적 + 오버레이 영상
```

오케스트레이션 방식은 `_step` 타이밍 래퍼로 각 단계를 감싸고, `lib/` 단계는 `run_in_container`, 외부 이미지는 GPU 지정 환경변수를 붙여 호출한다.

```python
# v2d_hoi_object_reconstruction/docker/run_reconstruction.py (발췌)
def _step(name, fn):
    t0 = time.time(); fn(); _timings[name] = time.time() - t0
    print(f"[pipeline] {name} done in {_timings[name]:.1f}s")

if args.mode == "bundlesdf" and not args.skip_stage1_nerf:
    _step("stage1_nerf", lambda: run_in_container(
        image=IMAGE_BUNDLESDF, module="v2d_bundlesdf.lib.reconstruct",
        inputs=_nerf_inputs, outputs={"output_path": stage1_recon_dir},
        extra_args=_bundlesdf_extra_args(),
        env={"CUDA_VISIBLE_DEVICES": str(fp_gpu)}, gpus=True))
```

#### 품질 게이트

`docker/_trajectory_tools.py`가 컨테이너 안의 분석기(`lib/check_sfm_scan_quality.py`, `lib/detect_stage1_end.py`)를 감싸고, "게이트 실패"와 "검사기 크래시"를 구분해 호스트에 의미 있는 오류로 바꿔 준다. 임계값은 `docker/data/configs/hoi_pipeline.yaml`에 있다(예: 최소 키프레임 30, 최소 회전 스팬 600°, 역행 비율 상한 0.25). 두 바퀴 스캔이면 약 720°가 나와야 한다는 도메인 지식이 그대로 수치가 되어 있다.

#### 재시작(resume) 로직

세 겹으로 되어 있다.

1. 단계별 `--skip_*` 플래그 약 20개.
2. 건너뛴 단계의 **값** 복구. `--skip_stage1_detect`면 `stage1_detect_debug/result.json`에서 경계를 다시 읽는다.
3. **콘텐츠 해시 캐시.** `masks/.prompts.sha256`에 `prompts.json`의 해시를 저장해 두고, 프롬프트가 바뀐 경우에만 SAM2를 다시 돌린다.

#### 병렬화

`run_depth_workers`가 프레임 구간을 GPU 수만큼 나눠 FoundationStereo 컨테이너 N개를 띄우고, 깊이와 마스크는 2슬롯 `ThreadPoolExecutor`로 동시에 진행한다. GPU 슬롯은 `_pipeline_utils.py::detect_gpu_ids`가 `nvidia-smi`를 파싱해 배정한다. `v2d_cusfm/docker/gpu_compatibility.py::require_compatible_cusfm_gpus`가 Blackwell(sm_120)을 사전 차단한다.

#### SAM3D 모드

`--mode sam3d`는 1~4b 단계를 공유한 뒤, 방위각 빈마다 대표 프레임을 고르고(`select_sam3d_frames`), 프레임별 단일 이미지 3D 추론, Stage-1 실루엣에 대한 스케일·회전·이동 피팅(`sam3d_srt`, Powell), 렌더 디버그, 최적 후보 선택(`select_sam3d_best`) 순으로 진행한다. 빠르지만 텍스처 완성도는 BundleSDF보다 낮은 대안 경로다.

#### 하위 모듈 진입점

- `v2d_cusfm/lib/image_list_to_sfm.py`: pyCuSFM 얇은 CLI. `create_cusfm_runner(...).run_all()` → `<output_dir>/keyframes/frames_meta.json`(포즈 포함).
- `v2d_bundlesdf/lib/reconstruct.py`: 준비된 recon 폴더(`keyframes.yml`, `left/`, `depth/`, `masks/`)를 검증하고, `config_resolver.py`로 `nerf.far: auto` 등을 마스크된 깊이에서 풀어 `resolved_config.yaml`을 남긴 뒤, `NVBundleSDF`로 SDF 학습 → 텍스처 베이킹 → GLB 내보내기. 포즈 추적(BundleTrack)은 지원하지 않고 외부 포즈만 소비한다.

### 3.6 Egocentric 파이프라인

1인칭 영상에서 **손(MANO) + 객체 메시/포즈 + 카메라 궤적**을 뽑아 `result_bundle`로 묶는 경로다. 세 겹의 스크립트로 되어 있다.

| 파일 | 역할 |
|---|---|
| `v2d_pipelines/run_ego_reconstruction.py` | 공개 진입점. `--hand_tracking {dynhamr,hamer}`로 아래 둘 중 하나를 고르고, 공통 후처리(DROID-SLAM, GeoCalib 중력 정렬, Three.js 내보내기)를 붙인다 |
| `v2d_pipelines/run_v2d_ego_e2e.py` | DynHaMR 경로. ViPE + Dyn-HaMR(`v2d_ego_hand_reconstruction`) → MoGe 깊이 → DINO → SAM2 → SAM3D 메시 → FoundationPose 스케일/추적 → EKF → 손 정렬 → `write_result_bundle` |
| `v2d_pipelines/run_ego_wilor.py` | HaMeR 경로(약 2300줄, 37단계). AnyCalib → GeoCalib → MoGe → DROID-SLAM → WiLoR → ... → HaMeR → gsplat 정제(`v2d_gsplat_refinement`) → 번들 |

이 파이프라인들의 재시작 관용구는 매우 단순하다. 각 단계를 "산출물이 이미 있는가"라는 술어로 감싼다.

```python
# v2d_pipelines/run_ego_reconstruction.py (발췌)
def _step(label: str, done: bool) -> bool:
    if done: print(f"  [skip] {label}"); return True
    print(f"  [run ] {label}");  return False
```

이 `[run ]/[skip ]` 마커는 1단계 `reconstruction_interface`가 stdout을 그대로 물려받아 웹앱 진행률 표시에 쓴다. 후처리 합류점은 다음과 같다.

```python
def _finalize_result_bundle(args, base_result_dir, *, dynhamr):
    final_result_dir = base_result_dir
    if args.run_droid_slam:          # 단안 궤적을 MoGe 깊이에 스케일 정렬
        ...
    if args.run_gravity_alignment:   # GeoCalib 중력으로 Z-up 정렬 (멱등)
        final_result_dir = _gravity_align_stage_result(args, final_result_dir, suffix)
    return final_result_dir
```

`v2d_ego_hand_reconstruction/`은 IsaacTeleop에서 벤더링한 ViPE/Dyn-HaMR 소스를 감싸는 호스트 전용 패키지로, MANO 자산을 컨테이너가 기대하는 위치에 스테이징한 뒤 업스트림 셸 스크립트를 그대로 실행한다.

### 3.7 `v2d_task_library_loader`: 3단계로 넘어가는 다리

공개 손-객체 데이터셋(taco, arctic, oakink2, hot3d, h2o, grab, dexycb)을 **MANO 순기구학**으로 풀어 `{dataset}_loaded` Parquet로 만드는 모듈이다. 로봇 손은 아직 등장하지 않는다.

이 모듈이 `reconstruction/`에 있는 이유는 **라이선스**다. MANO 순기구학(manotorch)은 GPL-3.0이라 별도 이미지에 격리하고, `robotic_grounding`은 manotorch를 절대 import하지 않는다.

- 호스트: `docker/run_loader.py::run_loader(dataset, output_dir, mano_model_dir, human_motion_data_dir, object_assets_dir, ...)`. MANO 디렉터리와 원본 데이터, 객체 자산 루트를 마운트한다.
- 컨테이너: `lib/run_loader.py`가 `--dataset`으로 `lib/loader_registry.py::LOADER_MODULES`를 조회해 데이터셋별 로더를 동적 import한다.
- 엔진: `lib/dataset_loader_base.py::DatasetLoaderBase(ABC)`. 데이터셋별 로더는 `list_sequences`, `load_mano_data`, `load_object_data`, `get_frame_object_poses` 등 훅만 구현하고, 공통 `run()` 루프가 프레임마다 MANO FK → 접촉점 계산(`contact_utils.py`) → `log_timestep`을 한 뒤 `sequence_id`, `robot_name`으로 파티션한 Parquet를 쓴다.

출력 컬럼은 좌/우 대칭으로 `mano_{left,right}_{trans, global_orient, finger_pose, joints, joints_wxyz, tips_distance, link_contact_positions, object_contact_positions, ...}`와 객체 컬럼 `object_body_position`, `object_body_wxyz`, `object_articulation` 등이다. 이 스키마(`ManoSharpaData`)는 **다운스트림인 `robotic_grounding.retarget`가 소유**하고, 이 모듈은 그것을 채우기만 한다.

---

## 4. 3단계: Robotic Grounding

> 위치: `robotic_grounding/`. 설치 패키지는 `source/robotic_grounding/robotic_grounding/`(Isaac Lab 확장), 진입점은 `scripts/`.

목표: 사람의 손-객체/전신 모션을 로봇(Sharpa Wave 손, Unitree Dex3 손, Unitree G1 휴머노이드)에 **리타게팅**하고, 그 참조 모션과 재구성된 씬으로 **Isaac Lab에서 RSL-RL PPO 정책을 학습**한다.

### 4.1 두 개의 도커 이미지와 오케스트레이터

```
원본 데이터셋 + MANO ──► [IMAGE 1: v2d_task_library_loader] ──► {ds}_loaded (Parquet)
                          stage: load (MANO 순기구학, GPL)
                                                                        │
{ds}_loaded ──► [IMAGE 2: robotic-grounding] ──► {ds}_processed  ◄──────┘
                 segment → urdf → processed → support → vis → dummy → assess
```

| 이미지 | 정의 위치 | 단계 | 이유 |
|---|---|---|---|
| `v2d_task_library_loader` | `reconstruction/modules/v2d_task_library_loader/docker/` | `load` | GPL MANO 코드 격리 |
| `robotic-grounding:<tag>` | `robotic_grounding/workflow/Dockerfile` | 나머지 전부 | Isaac Lab 2.3.2 + pinocchio/pink IK + viser + ONNX Runtime |

**`workflow/Dockerfile`**은 `nvcr.io/nvidia/isaac-lab:2.3.2` 위에 의존성을 깐다. 눈에 띄는 점은 pinocchio 네이티브 스택(`pin==3.7.0`, `pin-pink==4.2.0`, 모든 `cmeel-*`)을 **완전히 고정**했다는 것이다. 주석에 따르면 cmeel을 풀어 두면 soversion이 어긋나 `liburdfdom_sensor.so.4.0` 누락으로 런타임에 죽는다. QP 솔버는 `qpsolvers[clarabel,daqp,proxqp,scs,osqp]`, SONIC/motionbricks용 `onnxruntime-gpu`, Isaac Lab 호환을 위한 `numpy<2.0` 고정. 마지막에 `/usr/local/bin/python`을 `isaaclab.sh -p`로 exec하는 shim으로 만들어 컨테이너 안에서 `python foo.py`가 곧 Isaac Python이 되게 한다.

**`workflow/run.sh`**는 `build/start/shell/exec/stop`을 제공하는 컨테이너 생명주기 관리자다. 호스트 UID:GID로 실행하기 위해 컨테이너별 `/etc/passwd`를 합성하고, Kit 캐시 디렉터리를 호스트에 바인드하며, `HUMAN_MOTION_DATA_DIR`의 **하위 디렉터리를 하나씩** `assets/human_motion_data/<name>`에 마운트한다. 루트를 통째로 덮으면 레포에 커밋된 `whole_body/` 샘플이 가려지기 때문이다.

**`scripts/run_pipeline_docker.py`**(약 830줄)가 호스트에서 모든 단계를 지휘한다. `ALL_STAGES = [load, segment, urdf, processed, support, vis, dummy, assess]`이고, 데이터셋별 `RECOMMENDED_STAGES`가 `--stages auto`의 기본값이 된다(예: arctic은 관절형 객체 URDF가 이미 제공되므로 `urdf` 생략). `load`만 reconstruction 레포의 호스트 래퍼를 서브프로세스로 부르고, 나머지는 `_rg_docker()`가 `docker run ... --entrypoint /bin/bash <image> -lc "<inner>"`를 조립한다.

```python
# scripts/run_pipeline_docker.py (발췌)
def stage_processed(args, ds, dry):
    """PROCESSED stage: IK-retarget {ds}_loaded -> {ds}_processed (robot joints)."""
    p = _c_paths(ds)
    _require_sequences(args, ds, p["retarget_input"], dry)
    inner = _inner(["python", "scripts/retarget/run_retarget.py",
                    "--dataset", ds, "--robot", args.robot,
                    "--input_dir", p["retarget_input"], "--output_dir", p["processed"],
                    "--device", "cuda:0", "--save"] + _retarget_filter_flags(args))
    _run(_rg_docker(args, inner), dry)

STAGE_FNS = {"load": stage_load, "segment": stage_segment, "urdf": stage_urdf,
             "processed": stage_processed, "support": stage_support,
             "vis": stage_vis, "dummy": stage_dummy, "assess": stage_assess}
```

`_c_paths(ds)`가 컨테이너 안 경로 맵을 한 곳에서 관리한다(hot3d는 `segment` 단계를 거쳐 `_loaded_segmented`를 입력으로 삼는다). 객체 자산은 `/data/object_assets`와 레포 안 `assets/{meshes,urdfs}/<ds>` 두 곳에 동시에 마운트되어 생성물이 데이터 루트에 남고 레포는 깨끗하게 유지된다.

### 4.2 데이터셋 레지스트리와 리타게팅 (IK)

#### `retarget/dataset_registry.py`: 단일 진실 원천

frozen `DatasetConfig` dataclass들의 딕셔너리 `DATASET_CONFIGS`. 파이프라인, URDF 생성, 학습 자산 검증이 모두 여기를 본다. 새 데이터셋을 추가하려면 (1) 여기에 항목, (2) reconstruction에 로더, (3) `scripts/retarget/<name>_to_sharpa.py` 세 가지만 만들면 된다.

```python
# retarget/dataset_registry.py (발췌)
"arctic": DatasetConfig(
    name="arctic", fps=30.0,
    mano_kwargs={"flat_hand_mean": False, "center_idx": None},
    mesh_vertex_scale=1.0, mesh_format="obj",
    has_articulated_objects=True, has_contact_data=True,
    link_to_site_quat_wxyz=(0.5, -0.5, 0.5, 0.5),      # MANO 링크 → 로봇 사이트 손목 오프셋
    retarget_scripts={
        "sharpa_wave": "scripts/retarget/arctic_to_sharpa.py",
        "dex3":        "scripts/retarget/arctic_to_dex3.py",
    },
),
```

#### `scripts/retarget/run_retarget.py`: 디스패처

IK 코드는 한 줄도 없다. `--dataset`/`--robot`으로 레지스트리에서 스크립트 경로를 찾아 `importlib`로 동적 import하고, 그 모듈의 `parse_args()`/`main(args)`를 부른다. 그래서 데이터셋별 스크립트는 정확히 이 두 심볼만 노출하면 된다.

#### 리타게팅 알고리즘: pink 기반 미분 IK

라이브러리는 **pinocchio + pink**, QP 솔버는 기본 `daqp`다. 샘플링 기반 최적화가 아니라 매 반복 태스크 공간 QP를 푸는 미분 IK다.

`retarget/hand_kinematics.py::HandKinematics`(추상 베이스)가 **free-flyer 루트 관절**을 가진 `pin.RobotWrapper`를 만든다. 즉 손은 공중에 떠 있고, 상태는 `[위치(3), 쿼터니언 xyzw(4), 손가락 관절(N)]`이다. 로봇별 서브클래스는 네 개의 훅만 덮어쓴다.

| 서브클래스 | 모델 로딩 | 비고 |
|---|---|---|
| `SharpaHandKinematics` | `BuildFromMJCF(right_sharpawave.xml, FreeFlyer)` | 22 DoF 손가락 |
| `Dex3HandKinematics` | `BuildFromURDF(dex3_{side}.urdf, FreeFlyer)` | 3지 손, 손바닥 프레임 180° 보정 상수 |
| `WholeBodyKinematics` (`whole_body_kinematics.py`) | `robot_config.load_robot_config("g1")` | G1 전신. 코드에 로봇 분기 없이 JSON 설정 주도 |

매핑의 각 항목은 pink `FrameTask(frame_name, position_cost, orientation_cost)`가 되고, 목표는 변환·스케일된 MANO 관절 위치다. 핵심 루프는 다음과 같다.

```python
# retarget/hand_kinematics.py (발췌, 약 370~405행)
self.configuration.q = self.robot.q0.copy() if qpos is None else qpos.copy()
for _ in range(self.max_iter):
    vel = solve_ik(configuration=self.configuration, tasks=tasks, dt=self.dt,
                   solver=self.solver, safety_break=False, limits=self.configuration_limits)
    self.configuration.integrate_inplace(vel, self.dt)
    for task_name, task in self.frame_tasks.items():
        pos_error = float(np.linalg.norm(np.asarray(task.compute_error(self.configuration))[:3]))
        if abs(pos_error - frame_tasks_pos_error[task_name]) < self.frame_tasks_converged_threshold:
            frame_tasks_converged[task_name] = True
        frame_tasks_pos_error[task_name] = pos_error
    if all(frame_tasks_converged.values()):
        break
return {"q": ..., "frame_pose": ..., "frame_task_errors": ..., "num_optimization_iterations": ...}
```

수렴 판정은 절대 오차가 아니라 **태스크별 위치 오차의 변화량**이다. 반환되는 `frame_pose`는 pinocchio 모델의 **모든 프레임**의 월드 포즈로, 나중에 RL 보상 계산에 쓰이는 "67개 태스크 공간 참조 프레임"이 바로 이것이다. 프레임 간에는 이전 해를 초기값으로 쓰는 warm-start(`retarget_utils.py::run_frame_ik`)가 적용된다.

#### 손끝 매핑 (`retarget/params.py`)

`로봇 프레임 패턴 → (MANO 관절, 위치 비용, 방향 비용)`. 손끝이 지배적(1.0)이고, 중간 관절은 약한 자세 앵커(0.1), 방향은 손목에서만 의미 있게 가중된다.

```python
SHARPA_TO_MANO_MAPPING = {
    ".*_hand_C_MC":         ("wrist",   0.2, 0.2),
    ".*_thumb_MCP_VL_site": ("thumb2",  0.1, 0.0),
    ".*_thumb_tip_site":    ("thumb4",  1.0, 0.05),
    ".*_index_MP_site":     ("index1",  0.1, 0.0),
    ".*_index_tip_site":    ("index4",  1.0, 0.1),
    ".*_middle_tip_site":   ("middle4", 1.0, 0.1),
    ".*_ring_tip_site":     ("ring4",   1.0, 0.1),
    ".*_pinky_tip_site":    ("pinky4",  0.5, 0.1),   # 소지는 낮게
}
DEX3_TO_MANO_MAPPING = {                             # 3지 손
    ".*_hand_palm_link": ("wrist", 1.0, 0.1),
    ".*_thumb_tip": ("thumb4", 1.0, 0.0), ".*_index_tip": ("index4", 1.0, 0.0),
    ".*_middle_tip": ("middle4", 1.0, 0.0),
}
```

G1은 유일하게 매핑이 JSON(`retarget/configs/g1/retargeter.json`)으로 외부화되어 `robot_config.py::RobotRetargetConfig`로 파싱된다. 발은 비용 5(지면 접촉 우선), 손 1, 무릎 0.25이고, `PostureTask` 두 개(`q0` 정규화, 이전 프레임 추종)가 비용이 0보다 클 때만 생성된다.

#### 데이터셋별 드라이버

`scripts/retarget/arctic_to_sharpa.py::main()`이 일곱 개 `*_to_sharpa.py`의 템플릿이다. 양손 `SharpaHandKinematics`를 만들고, 시퀀스마다 `ManoSharpaData.from_parquet(...)`로 읽어 프레임 루프에서 `run_frame_ik`를 호출하며 6개 시계열을 손마다 쌓는다. free-flyer의 쿼터니언은 xyzw이므로 저장 시 wxyz로 재정렬한다.

```python
robot_right_wrist_position.append(right_results["q"][:3].tolist())
robot_right_wrist_wxyz.append(right_results["q"][3:7][[3, 0, 1, 2]].tolist())  # xyzw -> wxyz
robot_right_finger_joints.append(right_results["q"][7:].tolist())
robot_right_frames.append(right_results["frame_pose"].tolist())
```

`scripts/retarget/soma_to_g1.py`(약 1240줄)는 전신 경로다. SOMA 신체 파라미터 + 객체 메시 + `poses.npy`를 읽고, 첫 프레임 앵커로 정규화한 뒤 같은 변환을 객체 궤적에도 적용해 손-객체 상대 포즈를 보존한다. reconstruction이 남긴 `ground_plane.json`을 변환 체인 전체로 통과시켜 지면 정렬(`retarget/ground_alignment.py`)을 하고, 프레임마다 `WholeBodyKinematics.compute()`를 돌려 `motion_v1` Parquet를 쓴다.

**주의할 점**: 손 파이프라인(`*_to_sharpa.py`)은 레거시 `ManoSharpaData` 포맷(`retarget/data_logger.py`)을 쓰고, `soma_to_g1`, `arctic_to_dex3`, 플래너만 `motion_v1`을 쓴다. `workflow/data_pipeline.md` 첫머리에 명시되어 있다.

### 4.3 모션 교환 포맷 `motion_v1`

> `source/robotic_grounding/robotic_grounding/motion_schema/{schema,reader,writer}.py`

생산자(리타게터, 플래너)와 소비자(학습 로더, 리플레이, 지지면 재구성, 시각화)가 공유하는 단일 Parquet 스키마다. 불변 규약: **쿼터니언은 어디서나 wxyz**, 포즈는 `[x,y,z,qw,qx,qy,qz]` 7-벡터, 시계열은 `(T, ...)`.

```python
# motion_schema/schema.py (발췌)
_POSE7 = pa.list_(pa.float32(), 7)
METADATA_FIELDS = [("schema_version", pa.string()), ("sequence_id", pa.string()),
                   ("robot_name", pa.string()), ("motion_kind", pa.string()), ("fps", pa.float32()), ...]
ROBOT_FIELDS  = [("robot_joint_names", pa.list_(pa.string())),
                 ("robot_root_position", _ts(_VEC3)), ("robot_root_wxyz", _ts(_VEC4)),
                 ("robot_joint_positions", _ts(pa.list_(pa.float32())))]
EE_FIELDS     = [("ee_link_names", pa.list_(pa.string())), ("ee_pose_w", _ts(pa.list_(_POSE7)))]  # (T,E,7)
HAND_FIELDS   = [("hand_sides", ...), ("hand_frames_w", ...), ("hand_finger_joints", ...)]        # per-side
ALL_FIELDS = METADATA + ROBOT + EE + HAND + OBJECT + CONTACT + SOURCE + DIAGNOSTICS
def build_schema() -> pa.Schema: return pa.schema(ALL_FIELDS)
```

- **`motion_kind` 판별자**: `single_robot`(전신 관절 상태 필수) vs `dual_hand`(손목 + 손 프레임 필수). `required_fields_for(kind)`가 필수 필드를 분기하고, `resolve_motion_kind()`는 **추론을 거부**한다. 태그 없는 옛 파일은 `MissingRequiredField`로 실패하고, 마이그레이터는 제공하지 않는다.
- **`MotionData` dataclass**: 인메모리 계약. 디스크의 `hand_sides` 인덱스 리스트를 `left_*`/`right_*`로 평탄화해 `tracking_command.py`가 그대로 소비한다.
- **Writer** `save_motion_parquet(md, root, partition_cols=["sequence_id","robot_name"])`: 필수 필드와 쿼터니언 정규화를 검사한 뒤 zstd 압축 Hive 파티션으로 쓴다.
- **Reader** `load_motion_data_parquet(path, device)`: 파일/파티션 디렉터리/데이터셋 루트를 모두 받고, pyarrow가 파일 본문에서 제거한 파티션 컬럼을 디렉터리 이름에서 복원한다.

디스크 레이아웃: `whole_body/{dataset}/sequence_id={seq}/robot_name={robot}/data.parquet`.

### 4.4 지지면 재구성과 URDF 생성

#### `scripts/reconstruct_support_surfaces.py` + `retarget/support_recon.py`

객체가 **어디에 놓여 있었는지**를 알아내어 그 아래에 충돌 지오메트리(탁자)를 깔아 준다. 없으면 객체가 바닥으로 떨어지고 접촉 보상이 무의미해진다.

1. 프레임 간 이동 < 1 mm, 회전 < 0.01 rad인 프레임을 "정지"로 판정하고 5프레임 이상 연속인 구간만 남긴다.
2. (H2O만) 손이 잡고 있는 구간을 제외하는 게이트.
3. 정지 구간마다 메시 정점을 월드로 변환해 X-Y AABB 중심, **최소 Z**, 반경을 갖는 디스크를 만든다(`compute_support_disk`).
4. 겹치는 디스크 병합, 다른 객체 궤적 위에 놓인 유령 지지면 제거, 바닥 높이 디스크 제거.
5. `.usda`로 기록. 각 디스크는 `UsdGeom.Cylinder`에 `UsdPhysics.CollisionAPI`가 적용된다.

```python
cyl = UsdGeom.Cylinder.Define(stage, prim_path)
cyl.CreateAxisAttr(UsdGeom.Tokens.z); cyl.CreateHeightAttr(height); cyl.CreateRadiusAttr(radius)
UsdPhysics.CollisionAPI.Apply(cyl.GetPrim())
```

출력 `reconstructed_stage/{sequence_id}_support.usda`는 학습 시 `SceneConfig._discover_support_surface()`가 자동으로 찾아 씬에 넣는다.

#### `scripts/generate_rigid_urdfs.py`

원본 메시(OBJ/GLB/PLY)를 Isaac Sim이 스폰할 수 있는 **단일 링크 강체 URDF**로 바꾼다. 데이터셋별 `_discover_*_objects()`가 `{safe_name: (mesh, urdf)}`를 돌려주고, 객체마다 (1) trimesh로 읽어 미터로 스케일한 뒤 **STL로 내보내고**(Isaac Sim의 OBJ 파서가 Meshlab 포맷을 못 읽기 때문), (2) 시각/충돌 지오메트리가 같은 URDF를 f-string으로 생성한다(기본 질량 0.3 kg). 멱등적이며 기존 URDF는 건너뛴다. arctic은 관절형 객체라 제외된다.

### 4.5 Isaac Lab 태스크: Sharpa 플로팅 핸드

> `tasks/v2d/` (환경 cfg `v2d_hand_env_cfg.py`, MDP `mdp/`), `tasks/scene_utils/`

`tasks/__init__.py`가 `import_packages`로 하위 패키지를 모두 import하여 `gym.register`가 실행된다. 등록은 스톡 `ManagerBasedRLEnv`를 그대로 쓰고 cfg만 바꾼다.

```python
# tasks/v2d/config/sharpa_wave/__init__.py
gym.register(id="Sharpa-V2D-v0", entry_point="isaaclab.envs:ManagerBasedRLEnv",
             disable_env_checker=True,
             kwargs={"env_cfg_entry_point": sharpa_v2d_env_cfg.SharpaV2DEnvCfg,
                     "rsl_rl_cfg_entry_point": f"{agents.__name__}.rsl_rl_ppo_cfg:SharpaV2DPPORunnerCfg"})
```

#### 씬은 Parquet에서 자동 발견된다: `SceneConfig.from_motion_file`

씬에 대한 어떤 것도 손으로 쓰지 않는다. 로봇 이름, 객체(강체/관절형), URDF 경로, 지지면, 에피소드 길이가 모두 모션 파일에서 유도된다.

```python
# tasks/scene_utils/scene_config.py (발췌)
@classmethod
def from_motion_file(cls, motion_file: str) -> SceneConfig:
    motion_file = cls._resolve_motion_file(motion_file)        # 4-파트 축약 경로 해석
    data = pq.read_table(motion_file).to_pydict()
    partition = cls._parse_partition_path(motion_file)
    cls._validate_assets(data, motion_file)                    # Isaac 로딩 전에 빨리 실패
    object_type   = cls._detect_object_type(data)              # rigid vs articulated
    scene_objects = cls._build_scene_objects(data, object_type, motion_file)
    fixed_objects = cls._build_fixed_objects(motion_file)      # 지지면 .usda
    episode_length_s = cls._build_episode_length_s(data)
    return cls(...)
```

`apply_scene_config(env_cfg, scene_config, use_primitive_urdfs)`가 이 결과로 cfg를 변형한다. 로봇 스폰, 객체 스폰, 커맨드 연결, 접촉 센서 부착, 에피소드 길이 설정을 담당하며, cfg가 양손형인지 전신형인지에 따라 분기한다.

#### MDP 구성

- **행동**: 손마다 `JointResidualWithTrackingActionCfg`. 정책은 절대 목표가 아니라 **리타게팅된 참조 위의 잔차**를 낸다(손목 위치 스케일 0.05, 방향 0.15, 손가락 0.15).
- **관측**: 손목 위치/방향/속도, 손가락 관절 위치/속도, 객체 위치/방향, 커맨드, 이전 행동, 손목 기준 접촉 방향. 대부분 ±0.01 균등 노이즈.
- **보상**: 세 개의 추적 보상이 **가중치 0.0에서 시작**하고 커리큘럼이 올려 준다.

```python
# tasks/v2d/v2d_hand_env_cfg.py (발췌)
action_rate_l2 = RewTerm(func=isaac_mdp.action_rate_l2, weight=-5e-3)
object_keypoints_tracking_exp = RewTerm(func=mdp.object_keypoints_tracking_exp, weight=0.0, ...)
hand_keypoints_tracking_exp   = RewTerm(func=mdp.hand_keypoints_tracking_exp,   weight=0.0, ...)
hand_joint_pos_tracking_exp   = RewTerm(func=mdp.hand_joint_pos_tracking_exp,   weight=0.0, ...)
termination_penalty           = RewTerm(func=mdp.termination_penalty, weight=-100.0)
contact_wrench_support_reward = RewTerm(func=mdp.contact_wrench_support_reward, weight=10.0, ...)
unintended_contact_penalty    = RewTerm(func=mdp.unintended_contact_penalty, weight=-10.0, ...)
```

- **종료**: 시간 초과, 손목이 궤적에서 0.2 m 이탈, 객체가 0.2 m / 0.7 rad 이탈.
- **커리큘럼** (`FixedTimestepCurriculumCfg`): 학습 레시피의 심장이다. **가상 객체 제어(VOC)** 라는 보조 장치가 처음에는 객체를 참조 궤적대로 텔레포트해 주고, 반복 2000→15500에 걸쳐 스케일 `1.0 → 0.75 → ... → 0.0`으로 줄어드는 동안 객체 추적 보상 가중치는 `0.0 → 0.1 → ... → 1.0 → 20.0`으로 오른다. 정책은 먼저 객체가 대신 들려 있는 상태에서 손 자세를 배우고, 마지막에는 스스로 객체를 물리적으로 들어야 20배 보상을 받는다.

PPO 설정(`agents/rsl_rl_ppo_cfg.py`): 24 steps/env, 20000 반복, actor/critic `[1024,512,256,128]`, lr 1e-3 adaptive, KL 0.005.

### 4.6 Isaac Lab 태스크: G1 전신 (SONIC + RL 잔차)

> `tasks/v2d_whole_body/` (`base_env_cfg.py`, `config/sonic/g1/g1_sonic_env_cfg.py`, `mdp/`)

전신 휴머노이드는 처음부터 RL로 걷기까지 배우게 하지 않는다. 사전학습된 **SONIC** 전신 컨트롤러(NVIDIA, arXiv:2511.07820)가 기본 동작을 내고, RL은 그 위에 **잔차**만 더한다.

#### SONIC 컨트롤러 (`mdp/actions/sonic_actions.py::SonicPolicy`)

`assets/policies/sonic/{encoder_batched, decoder_batched}.onnx` 두 ONNX 그래프를 `onnxruntime` CUDA 프로바이더로 로드하고, torch 텐서의 `data_ptr()`을 직접 바인딩해 호스트 왕복 없이 추론한다. 인코더와 디코더 사이의 잠재 공간은 FSQ(finite scalar quantization) 토큰이다. `SONICActionBase`는 관절을 SONIC이 제어하는 29-DoF 몸통과 직접 제어하는 손가락으로 나눈다.

#### 잔차 행동 (`mdp/actions/sonic_joint_residual_action.py`)

```python
# process_actions (발췌)
sonic_actions = self._policy(sonic_obs)                          # encoder -> FSQ -> decoder
squashed      = torch.tanh(full_residuals) if self._use_tanh else full_residuals
sonic_with_residual = sonic_actions + squashed * self._residual_scale
self._processed_actions[:, self._sonic_joint_indices] = sonic_with_residual * self._scale + self._joint_pos_default
# 손가락: 커맨드의 참조 관절 + 자체 잔차
base_joint_pos = self._command.command_joint_pos_multi_future[:, 0, :]
self._processed_actions[:, self._direct_joint_indices] = (
    base_joint_pos[:, self._direct_joint_indices] + squashed_fingers * finger_scale)
```

설정은 `SONICActionCfg(action_type=JOINT_RESIDUAL, residual_scale=0.5, finger_residual=True, finger_residual_scale=0.15)`. 행동 변형은 일곱 가지가 구현되어 있지만 출시 설정은 `JOINT_RESIDUAL`이다.

#### 환경 구성

- `V2DEnvCfg`(`base_env_cfg.py`): 평면 지형, 200 Hz 시뮬 / 50 Hz 제어, `TrackingCommandCfg motion`(앵커 `pelvis`, 미래 10프레임 × 0.1 s), 리셋 이벤트 하나.
- `TrackingCommand`(`mdp/commands/tracking_command.py`): 중앙 데이터 허브. `motion_v1` Parquet를 읽어 관절 순서를 시뮬 순서로 재배열하고, 커맨드 목표, 미래 프레임 델타, VOC 감쇠, 리셋 프리즈, 행동 히스토리를 관리한다.
- `G1SonicEnvCfg`: G1 + Dex 손 + **지연 액추에이터 모델**(`assets/actuators/delayed_implicit_actuator.py`), 접촉 센서, 프레임 트랜스포머.

#### 보상과 두 가지 참조

`G1SonicRewardsCfg`는 거의 비어 있어 `SonicG1-v0`는 Hydra용 뼈대다. 두 서브클래스가 특화한다.

| 환경 | 참조 출처 | 보상 | 잔차 스케일 |
|---|---|---|---|
| `SonicG1-ReconBody-v0` | 3인칭 영상 MHR 재구성(신체 정확) | 앵커/관절/객체/EE 추적 + force closure | 0.15 |
| `SonicG1-ReconHand-v0` | EE 기반 플래너(손 정확) | 손 키포인트, 손가락 관절, 접촉 추적 | 0.5 |

추적 보상은 가우시안 커널이다. 예: `motion_hand_keypoints_gaussian_exp`는 양손의 `[손목 ⊕ 손끝]` 오차에 대해 `exp(-‖err‖²/σ²)`를 합산한다. 종료는 앵커 위치 0.70 m, EE 0.15 m, 객체 0.10 m 등.

#### 3단계 ReconHand 학습 레시피 (태스크 등록에 내장)

| 단계 | 태스크 | 물리/보상 변경 |
|---|---|---|
| 1 워밍업 | `SonicG1-ReconHand-Stage1-v0` | 로봇↔객체 **충돌 끔**, VOC 항상 켬, 손 키포인트 + 손가락 관절 보상만. `--zero-actor`로 시작 |
| 2 접촉 접지 | `Stage2` (Stage1 체크포인트 이어서) | 충돌 켬, VOC 0.5에서 감쇠, 접촉 보상 활성(`contact_wrench_support_reward=5.0`, 미접촉 페널티 -5.0), 객체 키포인트 가중치 램프 |
| 3 전체 파인튠 | `Stage3` (기본 ReconHand 확장) | 항상 첫 프레임에서 리셋, VOC 끔, 객체 키포인트 가중치 5.0 |

README는 **평가는 기본 태스크로** 하라고 경고한다. 스테이지 태스크는 물리 변경을 굽어 넣었지만 관측/행동 공간은 같으므로 체크포인트는 그대로 로드된다.

### 4.7 전신 플래너: `planner/g1_planner.py`

리타게팅된 **Dex3 양손 EE 궤적**(`arctic_to_dex3` 출력)을 **G1 전신 참조 모션**으로 바꾼다. 전신 모션캡처가 없는 손-객체 데이터셋에서도 ReconHand 환경을 쓸 수 있게 하는 다리다.

학습된 모델은 **motionbricks**(`planner/motionbricks/`). `MotionInferenceAgent`가 root/pose/decode ONNX 그래프를 감싸고, 토큰화된 자기회귀 방식으로 `infer_from_ee_positions(root, l_ee, r_ee, ...)` → `qpos (T, 36)`을 낸다. `main()`의 흐름:

1. MuJoCo로 G1 정지 자세의 손목 위치 계산(`get_nominal_ee`).
2. V2D 참조 로드. 첫 접촉 기준으로 앞뒤를 자를 수 있다(`--v2d_start_at_first_contact`, `--v2d_pre_contact_frames`).
3. 작업공간 오프셋과 헤딩 정렬로 G1 좌표계로 변환.
4. 정지 자세 유지 → 보간 → 참조 시작 유지 → 참조 순으로 접근 궤적을 붙인다(`trajectory.py::build_interp_trajectory`).
5. 여러 요(yaw) 오프셋 가설로 추론을 돌려 **손목 추적 오차가 최소인 것을 선택**.
6. 플래너의 29-DoF 몸통과 참조의 손가락 관절을 합쳐 전체 qpos 구성(`utils/qpos.py`).
7. `save_planner_parquet()` → `motion_v1`. 저장 전 `utils/validation.py`가 계약 위반 시 하드 실패.
8. `support_recon`을 재사용해 지지면 `.usda`도 함께 생성.

출력은 `arctic/planner_processed/sequence_id=<seq>/robot_name=g1_dex3/`와 `reconstructed_stage/<seq>_support.usda`. README는 v0.2이며 발 미끄러짐이 알려진 한계라고 적는다.

### 4.8 RL 진입점: `scripts/rsl_rl/`

| 스크립트 | 하는 일 | 체크포인트 | 학습 |
|---|---|---|---|
| `dummy_agent.py` | **제로 액션**으로 환경 실행. 자산 로드, 씬 구성, 시뮬 진행을 검증 | 없음 | 아니오 |
| `train.py` | RSL-RL 학습 루프. `logs/rsl_rl/<run>/model_*.pt` | `--resume` 시 | 예 |
| `eval.py` | 체크포인트 로드, 평가, 정책 내보내기(JIT/ONNX) | 필수 | 아니오 |

공통 구조: argparse → `AppLauncher`(Omniverse import 전에 SimulationApp 필수) → `@hydra_task_config`로 등록된 cfg 구체화. 환경 구성은 세 스크립트가 동일하며, 여기서 `--motion_file`과 `--use_primitive_urdfs`가 씬으로 흘러든다.

```python
# scripts/rsl_rl/train.py (발췌)
if args_cli.motion_file is not None:
    env_cfg.motion_file = args_cli.motion_file
if hasattr(env_cfg, "motion_file") and env_cfg.motion_file is not None:
    scene_config = SceneConfig.from_motion_file(env_cfg.motion_file)
    apply_scene_config(env_cfg, scene_config, use_primitive_urdfs=args_cli.use_primitive_urdfs)
```

- **`--motion_file` 축약 경로**: `arctic/arctic_processed/dataset_s07_box_grab_01/sharpa_wave` 같은 4파트 문자열을 `SceneConfig._resolve_motion_file`이 `sequence_id=.../robot_name=...` Hive 파티션으로 확장한다(절대 경로, CWD 상대, `HUMAN_MOTION_DATA_DIR` 상대 순으로 시도).
- **`--use_primitive_urdfs`**: 객체별 URDF 대신 원시 충돌 형상을 스폰해 `urdf` 단계 없이 스모크 테스트를 가능하게 한다.
- `train.py`는 `RslRlVecEnvWrapper` → `OnPolicyRunner`로 감싸고, `--zero-actor`(actor 마지막 층 0 초기화, Stage 1용), `--set_std`, 분산 학습, W&B 재개를 지원한다.
- `eval.py`는 `export_policy_as_jit`/`export_policy_as_onnx`로 `<ckpt_dir>/exported/policy.{pt,onnx}`를 내보낸다. 이것이 실로봇 배포 산출물이다.
- `dummy_agent.py`의 `--success_marker`는 녹화 루프가 정상 종료되고 MP4가 존재할 때만 센티널 파일을 쓴다. CUDA assert나 타임아웃 KILL은 파일을 남기지 못하므로, 이 파일의 존재가 "끝까지 재생됐다"는 증명이 된다. 파이프라인의 `dummy` 단계와 품질 검사가 이를 이용한다.

### 4.9 테스트와 데이터 품질 검사

- `tests/test_retarget_pipeline_e2e.py`가 파이프라인 게이트다. `load`를 제외한 모든 단계를 커밋된 fixture에 대해 실행한다. 대상은 **synthbox**(라이선스 없는 합성 데이터셋, `scripts/make_synthbox_fixtures.py`가 생성)뿐이다.
- `test_motion_schema*.py`는 `motion_v1` 왕복과 필수 필드 분기, `test_whole_body_kinematics_baseline.py`는 골든 파일 회귀, `test_train_e2e.py`는 GPU가 필요한 학습 스모크.
- **품질 검사 플러그인**: `scripts/data_quality_checks/__init__.py::discover_checks()`가 디렉터리를 스캔해 `check(data, **kwargs) -> {"pass", "score", "reason"}`를 노출하는 파일을 자동 등록한다. `hand_penetration`(볼록 껍질 부호 거리 + 캡슐 거리), `arctic_support_disks`, `dummy_agent_success`(센티널 확인). `scripts/data_assessor.py`가 `inspect.signature`로 인자를 주입해 전체 데이터셋에 적용하고 실패 시퀀스를 필터링한다.

---

## 5. 단계 간 데이터 계약 요약

| 경계 | 생산자 | 소비자 | 형식 |
|---|---|---|---|
| Ingestion → Reconstruction | `clips_final.jsonl` / `graph.db` | `reconstruction_interface/ego_e2e/run_ego_e2e.py` → `run_v2d_ego_e2e.py` | `IngestedSegment(segment_id, video_path, start_t, end_t, object_label)`. 객체 라벨이 DINO 프롬프트가 됨 |
| Reconstruction 모듈 간 | `lib/*.py` | `v2d_pipelines/*` | 역깊이 uint16 PNG, `CameraIntrinsics` JSON, 마스크 PNG, `Transform3d` JSON, `poses.npy (N,4,4)`, `bbox_track.pt` |
| Reconstruction → Grounding (손) | `v2d_task_library_loader` | `scripts/retarget/*_to_sharpa.py` | `{ds}_loaded` Parquet, `ManoSharpaData` 스키마(스키마 소유자는 `robotic_grounding.retarget`) |
| Reconstruction → Grounding (전신) | MHR/SOMA 내보내기, `ground_plane.json`, 객체 메시 | `scripts/retarget/soma_to_g1.py` | `soma_params.npz`, `poses.npy`, `textured_mesh.obj` |
| Grounding 내부 | 리타게터, 플래너 | `TrackingCommand`, `SceneConfig`, 리플레이, 지지면 재구성 | `motion_v1` Parquet (wxyz, 7-벡터 포즈, `motion_kind` 판별자) |
| Grounding → 배포 | `eval.py` | 실로봇 | `exported/policy.{pt,onnx}` |

---

## 6. 종합 평가

**잘 된 점**

- **격리의 일관성.** "호스트는 조립만, 컨테이너가 계산"이라는 규칙이 34개 모듈에 예외 없이 적용되고, `run_in_container` 하나로 수렴한다. GPL(MANO)을 별도 이미지로 분리한 것도 같은 원칙의 연장이다.
- **계약의 명시성.** 깊이 인코딩, 쿼터니언 순서, 포즈 7-벡터, `motion_kind` 판별자처럼 헷갈리기 쉬운 것들이 코드와 문서 양쪽에 고정되어 있다. `motion_v1` 리더가 추론을 거부하고 실패하는 선택은 장기적으로 옳다.
- **데이터에서 씬을 유도.** `SceneConfig.from_motion_file`이 Parquet 하나에서 로봇·객체·지지면·에피소드 길이를 모두 끌어내므로, 학습 커맨드가 `--motion_file` 하나로 끝난다.
- **학습 레시피의 코드화.** VOC 커리큘럼과 3단계 ReconHand 스테이지가 태스크 등록에 굽어 있어 재현이 쉽다.
- **재시작 가능성.** HOI 객체 재구성의 해시 캐시, Ego 파이프라인의 산출물 존재 검사, 파이프라인 오케스트레이터의 단계 선택이 긴 GPU 작업의 실패 비용을 낮춘다.

**주의할 점**

- 손 리타게팅(`*_to_sharpa.py`)은 아직 레거시 `ManoSharpaData`이고 `motion_v1`은 전신/Dex3/플래너 경로만 쓴다. 두 포맷이 공존하므로 소비자(`support_recon`, `replay_data`)는 스키마 감지 분기를 갖고 있다.
- `run_mv_hoi_reconstruction.py`에는 재시작 로직이 없다. 긴 rosbag 처리에서 중간 실패 시 처음부터 다시 돌아야 한다.
- HOI 파이프라인은 Blackwell(sm_120)을 지원하지 않는다(`v2d_cusfm`의 TensorRT/cuVSLAM 버전 한계). 빌드와 실행 양쪽에서 사전 차단된다.
- 논문에서 보고한 약 2시간 학습의 가속 구현은 이 릴리스에 포함되지 않았다(README 명시).
