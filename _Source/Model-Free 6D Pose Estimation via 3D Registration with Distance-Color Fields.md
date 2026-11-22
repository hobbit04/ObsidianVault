---
School:
  - POSTECH
Lab:
  - CVLab
venue: CVPR
---
[[CVPR27_Model_Free_6D_Pose_Estimation_via_3D_Registration 2.pdf]]
## Task
6D pose estimation. 그 중에서도 Model-free(CAD 등의 3d 모델링 정보 없음), single-reference(하나의 시점에서 촬영된 이미지 하나만을 이용) 방식의 estimation이 목적이다. 

Reference view, query view 두 개가 입력(object mask 포함)으로 들어오면 reference view에서 위치한 물체가 어떤 변환을 거쳐야 query view의 상태가 될지, 그 상대 포즈를 출력한다. 
## Previous Limits
1. **Reference view를 하나의 feature로 인코딩한 후 입력으로 넣는 방식:** 레퍼런스에서 보이는 표면만을 이용할 수 있어서 정확도가 overlap에 크게 의존한다. 물체의 3d mesh를 복원하는 과정이 없어서, 출력으로 내놓은 상대 포즈를 기하적으로 검증할 수 없음. 
2. **3d mesh를 만드는 방식:** Mesh를 완벽히 생성할 수는 없기 때문에 정렬, 스케일링 단계 등이 필요하고 오차도 쉽게 발생함. 렌더링을 한 후 비교하는 방식을 사용해서 느림.
3. **RANSAC 방식:** 두 시점에서 물체의 대응점들이 많아야 하는데, view가 많이 다를 경우 대응점이 적기 때문에 불안정함.
## Method


