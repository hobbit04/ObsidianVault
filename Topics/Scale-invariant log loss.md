---
tags:
  - LossFunction
  - ComputerVision
---
[[SiLog.pdf]]

단안 depth estimation은 ill posed 문제라, 물체의 크기를 특정해내는 것이 불가능하다. 따라서 모델의 예측이 ground truth와 scale 차이만 있다면, 이에 대해선 크게 페널티를 주지 않아야 한다는 아이디어에서 출발한 손실 함수다.

$$L_\text{SILog}​=\frac{1}{n}\sum_i d_i^2​−\frac{\lambda}{n^2}​(\sum_i d_i​), \text{where\ }d_i=\log \hat{d}_i-\log d_i$$ 
이때 $\lambda$는 $0$ ~ $1$ 사이의 값을 갖도록 하고, 논문에선 $0.5$를 사용한다. $1$이면 완전히 scale invariant 한 식이 되고, $0$이면 L2 loss가 된다.

## References
https://guillesanbri.com/Scale-Invariant-Loss/