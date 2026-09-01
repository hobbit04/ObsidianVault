---
tags:
  - Math
---
한국어로는 공분산 행렬이라고 부른다. 

$n$차원 데이터 분포가 있을 때, 각 차원의 방향으로 분산을 구할 수 있을 것이다. 예를 들어 $(x, y, z)$의 3차원 데이터라면 $x$ 방향만 고려했을 때의 분산, $y$방향만 고려했을 때의 분산 등을 각각 구할 수 있다.

여기서 covariance, 공분산은 서로 다른 차원 두 개를 함께 놓고 분산을 구한다. $x, y$를 고려해 분산을 구하면 이를 공분산이라고 하는 것이다. 이는 기호로 $\text{Cov}(x, y)$와 같이 나타내며 $\mathbb{E}[(x-\bar{x})(y-\bar{y})^T]$ 로 계산한다. 

그럼 Covariance Matrix는 Covariance를 원소로 하는 행렬로 이해할 수 있을 것이다. $n$차원 데이터에 대한 Covariance Matrix는 $n\times n$ 행렬로 정의된다. 그리고 $\text{Cov}(x, y)$가 입력의 순서에 상관없어야 하기 때문에 해당 행렬은 대칭행렬이 된다. 보통 $\Sigma$로 나타낸다. 

이 행렬은 고유값 분해를 한 결과의 의미를 알아야 한다.  
$$\Sigma=V\Lambda V^T$$
이때 $V$는 eigen vector 행렬이고 $\Lambda$는 eigen value 행렬이다. $V^{-1}$이 아닌 $V^T$로 쓸 수 있는 이유는 $\Sigma$가 대칭 행렬이라 $V$를 정규직교로 잡을 수 있기 때문이다. 

이때 가장 eigen value가 큰 eigen vector의 방향이 데이터가 가장 많이 퍼져 있는 방향이다. 이를 principal direction 이라고 한다. 가장 작은 eigenvalue에 대응되는 방향은 반대로 데이터가 가장 적게 퍼져 있는 방향이다. 

마지막으로 공분산 행렬은 항상 **Positive Semi-Definite** 이다. 줄여서 PSD라고도 하는 이 성질은, 대칭행렬 $M\in \mathbb{R}^{n\times n}$이 모든 $v\in \mathbb{R}^n$에 대해 $v^TMv \geq 0$을 만족하는 것을 의미한다. 공분산 행렬은 이 성질을 자동으로 만족하게 되는데, 아래 식을 통해 증명할 수 있다. $$u^T\Sigma u=u^T\mathbb{E}[(x-\bar{x})(x-\bar{x})^T]u=\mathbb{E}[(u^T(x-\bar{x}))^2]=\text{Var}(u^Tx) \geq 0$$이 되기 때문이다. 분산은 0보다 크거나 같을 수밖에 없으므로 공분산 행렬은 PSD를 만족한다. 또한 PSD를 만족하는 것과, 모든 $\lambda_i$가 0이상인 것은 필요충분조건이다. 