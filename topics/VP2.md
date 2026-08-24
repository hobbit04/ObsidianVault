---
tags:
  - ComputerVision
  - Metric
---
**Title: A CONTROL-CENTRIC BENCHMARK FOR VIDEO PREDICTION**

*A benchmark for action-conditioned video prediction*
Goal of this benchmark: 간단한 인터페이스, 즉 한번의 forward prediction call 만으로 평가하는 것
Main question is, "어떻게 action-conditioned 비디오 예측 모델들의 downstream robotic control을 비교할 수 있을까?"
기존 방법의 한계: 기존에는 perceptual하고 pixel-wise인 metrics을 사용했는데, 이는 로봇 조작을 위한 planning 이라는 downstream task에는 적합하지 않았음.

Robotic control의 다른 것들은 모두 동일하게 하고, video predictor만 다르게 하는 구조로 비디오 예측 모델의 성능을 평가할 수 있다. 

사용할 수 있는 분야:
1. Simulated environments
2. Specific start/goal task instance specifications
3. Training datasets of noisy expert video interaction data
4. Fully configured model-based control algorithm
(c.f., [[iVideo]]가 4번에 해당하기 때문에 이 metric이 사용됐다)

### Visual foresight
1. 주어진 프레임들을 기반으로 미래의 프레임들을 예측해서 생성함. 여기에는 iVideoGPT, CDNA 등의 모델이 들어갈 수 있음.
2. 예측된 이미지 시퀀스를 활용하여 reward를 평가, 혹은 비용 함수를 최소화 하도록 하는 행동 경로를 선택함. 대표적인 방법으로는 Model Predictive Control(MPC)가 있음.
3. 미래 이미지와 목표 이미지 간의 distance를 이용해 점수를 내고, 여기서 VP2가 등장함. 
4. 가장 점수가 높은 행동 경로(action sequence)를 선택하고 시퀀스의 첫 번째 행동을 수행함. 
5. 다시 1번으로 돌아가 예측 후 행동 진행
목표를 다르게 설정하는 것이 가능하기 때문에 하나의 모델을 여러 task에 대해 평가할 수 있음. Forward prediction을 할 때만 모델과 상호작용 하므로 특정 모델에 국한될 필요가 없음.


## VP$^2$ benchmark
---
> 기존 비디오 생성 metrics 들은 robotic manipulation 성능을 제대로 나타내지 못했다. 즉, 어떤 metric에서 높은 성능을 보인 모델이 robotic manipulation task에서는 성능이 다른 모델보다 좋지 않을 수 있었다. 이 문제를 해결하고자 이 benchmark가 제작되었다.

environment and task definitions, a sampling-based planner, and training datasets 으로 구성된다.
### Environment and task definitions
1. `robosuite`: tabletop setting
2. RoboDesk: a desk manipulation setting
모두 로봇 모델과 다양한 물체를 포함하고 있다.

**Task category**: 특정 환경에서 수행할 수 있는 의미 있는 작업의 유형으로, 시뮬레이터의 state을 기준으로 성
공 여부를 측정한다. e.g., 냉장고 문 열기. 
**Task instance**: 하나의 task category에 속하는 구체적인 작업 상황. 초기 상태 + goal image(RGB)

이 두가지를 추가함으로써 환경 다양성과 모델의 generalization, robustness를 평가할 수 있다. 

### Sampling-based planning
Visual foresight을 이용해 planning을 하게 된다. 
$I_g$: Goal image
$I_c$: Context frames. 이 논문에선 2개만을 이용한다.
$C$: Cost function
$\hat{f_\theta}=$ $\text{min}_{a_1, a_2, ..., a_T} \sum_{i=1}^T C(\hat{f}(I_c, a_{1:T})_i, I_g)$ : Video prediction model

사용한 sampling-based planner는 MPPI를 이용해 가능한 action sequences에서 샘플링을 한다.

### Training datasets
35 timesteps.
각각 256 x 256 RGB 이미지와 취한 행동을 포함.

## Analysis
---
서로 다른 video prediction 모델들을 비교하는 것 뿐만 아니라 절대적인 모델의 성능도 측정하고 싶다!
그래서 Simulator라는 부분을 추가시키는데, 이는 실제 행동으로부터 나온 이미지, 즉 정답에 해당한다. Video prediction model, planner, cost function 등 여러 요인이 VP$^2$ 성능에 영향을 미치므로, "만약 video prediction model이 완벽했다면 몇 점이 나왔을까?" 에 대한 답을 추가해 video prediction model의 절대적인 성능을 구할 수 있다.
![[Pasted image 20250704194407.png|600]]
