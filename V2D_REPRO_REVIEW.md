---
tags: [v2d, chord, code-review, reproduction]
repo: video_to_data
commit: 8b37535c
date: 2026-09-15
---

# V2D / CHORD 재현 검토 노트

> 대상: `~/Documents/Postech/2026 CVLab/Repos/video_to_data` @ `8b37535c`
> 목표: CHORD 논문(`docs/chord/chord.pdf`) 재현
> 관련: [[V2D_CODE_REPORT.md]]

---

## 0. 결론 요약

1. **CHORD의 핵심 방법은 전부 구현돼 있다.** 식(1)~(3), 페널티, VOC 커리큘럼 모두 `tasks/v2d/`에 존재.
2. **재현 가능한 경로는 "공개 데이터셋 → Sharpa 손"뿐이다.** 자체 영상 경로는 논문이 요구하는 inpainting 모듈이 미공개라 끊겨 있다.
3. `ManoSharpaData`가 CHORD 본선이고 `motion_v1`은 전신(G1) 전용이다. **둘을 섞지 말 것.**
4. 시간축(fps) 처리에 확인된 결함 2건이 있고, **그중 하나는 CHORD 경로 위에 있다.**

---

## 1. CHORD 방법 ↔ 코드 대응표

| 논문 | 코드 | 상태 |
|---|---|---|
| 식(1) 렌치 행렬 · 마찰 원뿔 | `tasks/v2d/mdp/utils.py:322`, `utils_jit.py:239` | ✅ |
| 식(2) support function σ | `utils.py::compute_wrench_space_support_function`, `utils_jit.py:313` | ✅ |
| 식(3) r_cws | `tasks/v2d/mdp/rewards.py:408 contact_wrench_support_reward` | ✅ |
| r_unintend | `rewards.py:442 unintended_contact_penalty` | ✅ |
| r_miss | `rewards.py:465 missed_contact_penalty` | ✅ |
| r_relative | `rewards.py:487 relative_object_pose_reward` | ✅ |
| VOC 어닐링 커리큘럼 | `tasks/v2d/mdp/curriculum.py:47-156` | ✅ |
| 사람 접촉 렌치 사전계산 | `commands/hand_object_commands.py:745` | ✅ |
| **r_fc (reduced force closure)** | `tasks/v2d_whole_body/mdp/rewards/contact_rewards.py:100 force_closure_reward` | ⚠️ **전신 경로에만** |
| **§3.2 inpainting (hand-only→전신)** | `grep -i inpaint` → **0건** | 🔴 미공개 |
| ~2시간 학습 가속 구현 | README가 미포함 명시 | 🔴 |

### r_fc 확인 결과 (2026-09-15)
- **구현 존재**: `force_closure_reward(env, command_name="motion", min_support=0.01)`
  - 논문 식과 일치: `has_support.float().mean(dim=-1)` = 기저 방향 중 support > ε 인 비율, ε=`min_support`=0.01
  - 등록·가중치: `config/sonic/g1/g1_sonic_env_cfg.py:561` `weight=5.0`
- **단, `tasks/v2d/`(Sharpa 손 = CHORD 본선)에는 없다.** 손 경로 `rewards.py`의 18개 함수에 force closure 없음.
- 논문 §3.2가 r_fc를 쓰는 두 경우 중 **(b) 전신 레퍼런스만 구현**, **(a) RGB 영상 재구성의 노이지 접촉은 손 경로에서 사용 불가**.
- 구현이 논문과 다른 점(docstring이 자인): *"proxy lower bound: support is evaluated per hand rather than by combining both hands' contacts into a single wrench space per body"* — 양손 접촉을 합쳐 하나의 렌치 공간으로 보지 않고 손별로 평가.
- 참고: CHORD 보상 세트가 **두 번 구현**돼 있다. `tasks/v2d/mdp/rewards.py`(손)와 `tasks/v2d_whole_body/mdp/rewards/contact_rewards.py:23,55,77`(전신). 중복 유지보수 리스크.

### 🟢 전신 경로에는 예제 데이터가 동봉돼 있다
`assets/human_motion_data/whole_body/` — **자체 촬영 영상에서 나온 3개 시퀀스가 이미 리타게팅된 상태로** 들어 있음:
- `soma/sequence_id={corn_can_right_left_handover_01, snack_box_pick_and_place_01, blue_trash_can_drag_007}/robot_name=g1/data.parquet` (motion_v1)
- 각 시퀀스에 `object/textured_mesh.{obj,urdf}` + 텍스처
- `reconstructed_stage/*_support.usda` 3개
- datacard: *"three post-processed examples from the HOI dataset, retargeted to the G1 robot"*

→ **2단계를 돌리지 않고도 전신 경로를 end-to-end로 재현 가능.**

### 하이퍼파라미터 대조 필요
- `contact_wrench_support_reward(tolerance=0.1, var=0.1)` — 논문 β, v_cws와 대조
- 렌치 기저 개수 b, 마찰 원뿔 edge 수 d
- 성공 판정: 논문은 position err > 15cm 또는 rotation err > 40°에서 종료, completion ratio > 0.7

---

## 2. 데이터 경로: 무엇이 이어지고 무엇이 끊겼는가

```
공개 DS(taco/arctic/oakink2/hot3d/h2o/grab/dexycb)
   └─ v2d_task_library_loader ─ <ds>_loaded ─ *_to_sharpa.py ─ ManoSharpaData ─▶ tasks/v2d/ (CHORD)   ✅ 유일한 완전 경로

MV-HOI rosbag ─ run_mv_hoi_reconstruction ─ soma_params.npz+poses.npy ─ soma_to_g1 ─ motion_v1 ─▶ G1 전신   ⚠️ 디렉터리명 불일치
                                                                        (object_mesh/ vs reconstructed_mesh/)

Ego 영상 ─ run_ego_* ─ result_bundle ─▶ export_result_threejs_scene.py 뿐           🔴 3단계 연결 0건
```

### 근거
- `result.npz`를 읽는 코드는 레포 전체에서 `export_result_threejs_scene.py:721` **단 하나**. `robotic_grounding/`에서 `result_bundle` 참조 **0건**.
- `loader_registry.py:11-19` — 공개 데이터셋 7종 전용. ego 로더 없음.
- `soma_to_g1.py:334-336`은 `reconstructed_mesh/output_aligned.glb`를 요구하나, `export_sequence.py:322`는 `object_mesh/`에 쓴다 → **수동 재배치 전제**.
- 논문 §3.2가 이 빈칸의 정체를 명시: *"For hand-only references, such as egocentric reconstructions, we train an **inpainting module** to predict full-body motion from end-effector trajectories"*

---

## 3. 모션 포맷 이음매

`ManoSharpaData`(레거시 명칭이지만 **CHORD 본선**) vs `motion_v1`(전신 전용).

- `motion_kind="dual_hand"`를 생산하는 코드는 **테스트에만 존재**. 실제 생산자는 `soma_to_g1.py:1072`와 `g1_planner.py:365`뿐이며 둘 다 `single_robot`.
- **마이그레이터가 없다.** `replay_data.py:265,287`이 `scripts/motion_schema/migrate_to_v1.py`를 실행하라고 안내하지만 **그 디렉터리·파일이 존재하지 않는다.** `schema.py:511`과 `motion_schema/README.md:135`는 정반대로 "no migrator is shipped, 재생성하라"고 한다. → **문서 버그, 보고 대상.**
- 마이그레이션은 구조적으로 불가: `dual_hand` 필수 필드 `ee_link_names`/`ee_pose_w`에 대응하는 개념이 `ManoSharpaData`에 없음.
- 잠복 버그: `MotionData.num_frames()`(`schema.py:437`)가 T를 `robot_root_position`에서만 유도 → `dual_hand` 파일은 항상 0.
- 좌/우 인덱스: `ManoSharpaData`는 right-first, `replay_data.py:159`는 `left_idx, right_idx = 0, 1` 기본. 명명 규약 미명세.
- 스키마 감지가 `replay_data.py:232`와 `support_recon.py:117` **두 곳에 중복 구현**.

---

## 4. 확인된 결함 (우선순위)

| #     | 위치                                                | 확신      | CHORD 경로? | 내용                                                                                                                                                                                                                                        |
| ----- | ------------------------------------------------- | ------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **F** | `tasks/v2d/mdp/utils.py:199`                      | 확실      | 🔴 **예**  | `interpolate_robot_motion_data`가 리샘플 후 `.fps`를 갱신하지 않음. 호출부 `hand_object_commands.py:214`. 120Hz GRAB/OAKINK2를 리샘플해도 `.fps`는 120 그대로 → `replay_motion.py:738,895`, `viser_playback.py:331`이 잘못된 시간축 사용                                    |
| **H** | `soma_to_g1.py:914,1075`                          | 확실      | 아니오(전신)   | `fps=float(kin.frequency)` — `kin.frequency`는 **IK 솔버 rate limiter 기본값 200.0**(`whole_body_kinematics.py:39`)이지 모션 fps가 아님. `soma_to_g1.py`에 `--fps` 인자 없음, `read_soma.py`는 npz의 framerate를 읽지 않음 → 30fps 영상이 `fps=200`으로 기록, 재생 ~6.7배 오차 |
| **A** | `dataset_registry.py:81,125,145`                  | 확실      | 예         | `link_to_site_quat_wxyz` 필드가 레포 전체에서 **한 번도 읽히지 않음**. 각 스크립트가 상수 하드코딩. 헬퍼 `retarget_utils.py:159`는 **xyzw**를 받는데 docstring은 "wxyz"라고 오기 → 향후 "중복 제거" 시 손목이 조용히 틀어짐                                                                        |
| **D** | `taco_loader.py:353` vs `dataset_registry.py:107` | 확실      | 예         | `mesh_vertex_scale`(TACO=0.01) 이중 진실 원천. 현재 값은 일치하나 동기화 장치 없음                                                                                                                                                                             |
| —     | `dataset_registry.py`의 `fps`                      | 확실      | 예         | `config.fps` 소비자 **0개**. 실제 fps는 `*_loader.py` 상수에서 옴. 동일 패턴의 이중 진실 원천                                                                                                                                                                    |
| **G** | `tracking_command_cfg.py:131`                     | 확실      | 아니오       | `target_fps` 필드가 소비되지 않음 → 전신 경로에 리샘플링 부재                                                                                                                                                                                                 |
| **B** | `soma_to_g1.py:792,800`                           | 의심(높음)  | 아니오       | world 회전에 `transform_source_rotation`(R@M@Rᵀ) 적용. 같은 프레임의 위치는 world 규약(`R@p`) → 위치/회전 basis 불일치                                                                                                                                           |
| **C** | `soma_to_g1.py:868-869`                           | 확실      | 아니오       | `soma_joints*`만 변환·높이 보정 없이 raw 저장 → parquet 내 좌표계 혼재                                                                                                                                                                                     |
| **E** | `read_soma.py:356` vs `soma_to_g1.py:359`         | 의심(조건부) | 아니오       | SOMA `unit` 스케일이 `transl`에만 적용, 객체 `poses.npy`엔 미적용. non-meter export 시 몸/객체 분리                                                                                                                                                           |
| —     | `v2d_viz/run_3d_viewer.py:94`                     | 확실      | 아니오       | 깊이 디코딩 `65535/(raw+1)-1` — 정식 `65535/raw-1`과 불일치(`datatypes.py:34`). 다른 12개 지점은 전부 정합. 뷰어 전용이나 시각 검증을 왜곡                                                                                                                                  |

### 정합성이 확인된 것 (안심해도 됨)
- 쿼터니언 재정렬: `*_to_sharpa.py:235,244`, `soma_to_g1.py:837`, `pinocchio_viser_visualizer.py:259`, `read_soma.py:223` 모두 정상
- 깊이 인코딩/디코딩: 뷰어 1곳 제외 13개 지점 전부 `datatypes.py:14-34`와 일치
- 앵커 정규화 → 객체 궤적 동일 변환 적용(`soma_to_g1.py:428-433`) → 지면 정렬(`ground_alignment.py:903`) 순서 및 변환 수학 정상
- MANO는 미터. `mano_to_robot_scale=1.2`는 단위 변환이 아니라 사람손→로봇손 체격비

---

## 5. 재현 가능한 두 트랙 (확정)

| | 트랙 A: 손 (Sharpa) | 트랙 B: 전신 (G1) |
|---|---|---|
| 논문 절 | §4.1–4.4 (주 실험, 82.12%) | §4.5 (90.77%) |
| 코드 | `tasks/v2d/` | `tasks/v2d_whole_body/` |
| 포맷 | `ManoSharpaData` | `motion_v1` (`single_robot`) |
| 데이터 | 공개 DS (arctic/hot3d/taco…) — 별도 다운로드 | **레포 동봉 3시퀀스** |
| 보상 | r_cws + r_unintend + r_miss + VOC | 위 + **r_fc**(weight 5.0) |
| 영상 유래? | 아니오 (mocap) | 예 (자체 HOI 촬영) |
| 착수 비용 | 중 (DS 셋업 필요) | **낮음 (즉시 실행 가능)** |

**트랙 B가 "영상 → 로봇 모션"에 가장 가까운, 실제로 돌아가는 경로다.** 단 2단계를 직접 돌리는 게 아니라 이미 처리된 산출물을 쓰는 형태.

## 6. 다음 액션

1. **트랙 B 먼저 실행.** 동봉 3시퀀스로 `g1_sonic_env_cfg` 학습을 띄워 환경·의존성·자산 로딩을 검증. 실패 비용이 가장 낮은 진입점.
2. **트랙 A 데이터 셋업.** `docs/{ARCTIC,HOT3D,TACO}_SETUP.md` → `run_example_sequences.sh`. 논문 1,831 태스크 중 실가용 개수 산정.
3. **하이퍼파라미터 대조.** 논문 Appendix vs `contact_wrench_support_reward(tolerance=0.1, var=0.1)`, 렌치 기저 개수 b, 마찰 원뿔 edge 수 d, 종료 임계(15cm / 40°).
4. **결함 F 수정** — 트랙 A 위의 유일한 확인된 시간축 버그. 특히 GRAB/OAKINK2(120Hz).
5. 자체 영상 → 전신은 **inpainting 모듈 부재로 불가**. 직접 구현하려면 별도 연구 과제로 분리.
