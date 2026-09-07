---
title: |-
  SPIDER: Scalable Physics-Informed
  Dexterous Retargeting
School:
  - Carnegie Mellon University
Lab:
  - FAIR at Meta
tags:
  - 3D
  - Robotics
---
## Task
> How can we efficiently and reliably transform human motion into feasible robot trajectories that respect dynamics and contact?

사람의 손 모션 데이터를 어떻게 로봇에 대입시킬 수 있을까에 대한 답을 제시한다. [[Do as I do]]에서의 reconstruction에 집중하는 것으로 볼 수 있다. 
## Method
크게 네 단계로 나누어 설명한다. 문제를 정의하고, 해결하는 방법을 제시하고, 효율과 퀄리티를 높이는 기법을 소개한 다음 마지막으로 시뮬레이션과 현실의 차이를 좁히기 위한 방법을 제시한다.
### Physics-based retargeting problem
어떻게 물리를 기반으로 retargeting을 해야 하는지, 최적화 문제로 먼저 정의한다. 