## Reconstruction 단계
**하는 일**
human video에서 손, 물체 메시 데이터를 추출해내는 것. Multiview, stereo 등의 환경에서 작업을 수행할 수 있지만 우리는 ego-centric data에서의 성능을 확인하려고 한다. 구체적으로 ego-centric video가 입력되면 프레임 단위로 
1. Depth
2. Object masks
3. Textured meshes
4. 6-DoF object poses
5. MANO hand parameters (SMPL human body parameters는 전신 파라미터)
를 얻는다.

**Data**![[tissue_box.mp4]]특징;
1. 카메라가 안 움직임
2. 물체 occulsion 거의 없음
3. 렌즈 왜곡 거의 없음(화면 중앙부분에서 대부분의 일이 일어남)

### Options
**`--undistort`** — AnyCalib으로 렌즈 왜곡을 추정해 영상을 보정한 뒤, 그 보정 영상을 이후 전 단계의 입력으로 씁니다. 광각·액션캠 촬영이면 필요하고, 왜곡이 작은 영상이면 생략 가능합니다. 비용: 컨테이너 1회 + 영상 재인코딩.

**`--run_droid_slam`** — DROID-SLAM으로 프레임별 카메라 궤적을 복원하고, MoGe depth에 스케일을 맞춥니다. **ego 영상에서 카메라가 움직이면 사실상 필수**입니다. 이게 없으면 물체 포즈가 카메라 좌표계에만 있고 월드 좌표계 궤적이 없습니다. gsplat refinement를 켤 경우 배경 pose field의 초기값으로도 쓰입니다. 비용: 프레임 수에 선형, GPU 메모리를 많이 먹는 편.

**`--run_gravity_alignment`** — GeoCalib으로 중력 방향을 추정해 결과 번들 전체를 중력 정렬된 좌표계로 회전시킵니다. 로봇 학습으로 넘길 거면 "위쪽이 어디인가"가 정의돼야 하므로 필요합니다. 비용: 작습니다(기준 프레임 위주 + 번들 변환).

**`--run_gsplat_refinement`** — 3D Gaussian Splatting으로 손·물체·카메라 포즈를 렌더링 손실 기준으로 동시 최적화합니다. 품질을 가장 크게 끌어올리지만 **전체 시간의 압도적 비중**을 차지합니다. 기본 10 epoch이고 `--gsplat_refine_epochs`로 조절합니다. 앞서 받아둔 VGG16이 여기 perceptual loss에 쓰입니다. 타이밍만 보는 게 목적이면 epoch을 줄여 돌리고 epoch당 비용을 따로 보고하는 편이 낫습니다.

**`--export_threejs_result`** — 결과를 브라우저에서 볼 수 있는 Three.js 씬으로 내보냅니다. MANO_RIGHT.pkl을 여기서 씁니다(오늘 채운 파일). 비용은 거의 없습니다.

**`--object_mesh` (+ `--skip_object_scale_estimation`)** — 물체 메시를 직접 주면 SAM3D 메시 생성 단계를 건너뜁니다. `--skip_object_scale_estimation`은 준 메시의 스케일을 신뢰하고 MoGe/FoundationPose 스케일 추정까지 생략합니다. 단계별 시간을 온전히 보려면 **쓰지 않는 게** 좋습니다.

**`--reference_frame`** — Grounding DINO 검출과 SAM3D 메시 생성의 기준 프레임. 물체가 손에 가리지 않고 잘 보이는 프레임을 고르면 품질이 올라갑니다. 기본 0.

**`--dev`** — 호스트의 `modules/`를 컨테이너에 마운트해 이미지 재빌드 없이 코드 수정을 반영합니다. 개발용이고, 측정에는 마운트 오버헤드가 섞이므로 **끄는 게 맞습니다**.



**명령어**
``` #1
cd ~/repos/video_to_data/reconstruction
export CUDA_VISIBLE_DEVICES=6,7
mkdir -p data/outputs

python -u modules/v2d_pipelines/run_ego_reconstruction.py \
  --video assets/tissue_box.mp4 \
  --output_dir data/outputs/timing_tissue_box \
  --object_prompt "a tissue box" \
  --hand_tracking hamer \
  --reference_frame 0 \
  --undistort \
  --run_droid_slam \
  --run_gravity_alignment \
  --export_threejs_result \
  2>&1 | tee data/outputs/run1_no_gsplat.log

```


## Robotic grounding 단계
