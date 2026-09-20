## Reconstruction 단계
### 하는 일
human video에서 손, 물체 메시 데이터를 추출해내는 것. Multiview, stereo 등의 환경에서 작업을 수행할 수 있지만 우리는 ego-centric data에서의 성능을 확인하려고 한다. 구체적으로 ego-centric video가 입력되면 프레임 단위로 
1. Depth
2. Object masks
3. Textured meshes
4. 6-DoF object poses
5. SMPL human body parameters
를 얻는다.

## Robotic grounding 단계
