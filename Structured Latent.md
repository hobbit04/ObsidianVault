---
tags:
  - 3D
  - ComputerVision
---
[[TRELLIS]]에서 처음 제시된 방법으로, 3d asset의 생성을 위해 사용된다.

3d asset은 크게 두 가지 정보가 있다. 기하(geometry) 정보와 외관(appearance) 정보가 그것이다. 컵을 예시로 들자면 컵이 원기둥처럼 생겼는지, 아니면 각졌는지 등은 기하 정보이고 표면의 색깔이나 그려진 무늬 같은 것은 외관 정보일 것이다. [[3D Representation]]의 종류에 따라 둘 중 하나의 정보에 강점을 갖는 것이 일반적이다. [[Mesh]]는 기하에 강하고, [[3D Gaussian Splatting]]은 외관에 강하다. 

Structured Latent, 줄여서 *SLAT*은 두 정보를 하나의 latent에 녹여내고자 한다. 하나의 asset은 하나의 unified SLAT를 갖게 된다. 이를 $z$라 하고, 정의는 다음과 같다. $$z=\{(z_i,p_i)\}^L_{i=1},\text{where } z_i \in \mathbb{R}^C,p_i\in\{0, 1, ...,N-1\}^3$$이때 $p_i$는 활성화 된, 즉 비어 있지 않는 [[Voxel]]의 positional index 이다. $z_i$는 해당 Voxel에 대응되는 local latent이다. $N$은 3D grid의 길이(voxel의 수)이고 $L$은 그 중 활성화 된, 표면이 존재하는 voxel의 수를 의미한다. 
