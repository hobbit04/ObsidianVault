---
tags:
  - ML
  - Attention
---
# Vector Attention

> **한 줄 정의**: 이웃 하나당 가중치를 **스칼라 1개**가 아니라 **채널 수만큼의 벡터**로 만들어서, feature의 채널마다 서로 다른 이웃을 참조하게 하는 어텐션.

[[Point Transformer]]에서 [[Point Cloud]]를 처리하기 위해 채택한 방식이다. 원래는 같은 저자의 이미지 논문(SAN, *Exploring Self-attention for Image Recognition*)에서 제안된 개념이다.

---

## 1. 왜 필요한가: Scalar Attention의 한계

기존 트랜스포머의 어텐션(scalar attention)은 이렇게 생겼다.

$$y_i = \sum_{x_j} \rho\big(\varphi(x_i)^\top \psi(x_j) + \delta\big)\, \alpha(x_j)$$

여기서 query와 key를 **내적**한다는 게 핵심이다. 내적은 $d$차원 벡터 두 개를 넣어서 **숫자 하나**를 뱉는 연산이다. 그래서 이웃 $j$에 대한 가중치는 스칼라 $w_{ij} \in \mathbb{R}$ 하나뿐이고, 곱셈은 이렇게 된다.

$$y_i = \sum_j w_{ij} \cdot \underbrace{\alpha(x_j)}_{d\text{차원}}$$

**문제**: $\alpha(x_j)$의 모든 채널이 **똑같은 배율** $w_{ij}$를 받는다. 이웃 $j$가 중요하면 그 이웃의 512개 채널이 전부 통째로 중요해지고, 안 중요하면 전부 통째로 죽는다. 즉 scalar attention이 던지는 질문은 딱 하나다.

> "이 이웃은 **얼마나** 중요한가?"

하지만 현실은 이렇지 않다. 어떤 이웃은 *색깔 정보*는 쓸모없는데 *기하 구조 정보*는 결정적일 수 있다. Scalar attention은 이걸 표현할 수단이 없다.

Vector attention은 질문을 하나 더 던진다.

> "이 이웃의 **어느 성분이** 중요한가?"

---

## 2. 수식 뜯어보기

논문의 일반형(Eq. 2)은 다음과 같다.

$$\mathbf{y}_i = \sum_{x_j \in \mathcal{X}} \rho\Big(\gamma\big(\beta(\varphi(x_i), \psi(x_j)) + \delta\big)\Big) \odot \alpha(x_j)$$

기호를 하나씩 풀면:

| 기호 | 역할 | 입력 → 출력 |
|---|---|---|
| $\varphi, \psi, \alpha$ | linear (= Q, K, V) | $\mathbb{R}^d \to \mathbb{R}^d$ |
| $\beta$ | **relation function**. 두 벡터의 관계를 만듦 (보통 뺄셈) | $\mathbb{R}^d \times \mathbb{R}^d \to \mathbb{R}^d$ |
| $\delta$ | position encoding | $\to \mathbb{R}^d$ |
| $\gamma$ | **mapping function** (MLP). 어텐션 벡터를 생성 | $\mathbb{R}^d \to \mathbb{R}^d$ |
| $\rho$ | normalization (softmax) | $\to \mathbb{R}^d$ |
| $\odot$ | 원소별 곱 (Hadamard) | |

**Scalar attention과 갈리는 지점은 $\beta$다.** 내적 $\varphi^\top\psi$는 차원을 1로 뭉갠다. 반면 뺄셈 $\varphi - \psi$는 **$d$차원을 그대로 유지**한다. 이 살아남은 $d$차원이 $\gamma$를 거쳐 최종적으로 $d$차원 가중치 벡터가 된다. 그래서 $\odot$(원소별 곱)이 가능해진다.

$$\underbrace{\varphi(x_i) - \psi(x_j)}_{d\text{차원 유지}} \;\xrightarrow{\;+\delta\;}\; \xrightarrow{\;\gamma\;}\; \underbrace{\text{score}_{ij}}_{d\text{차원}} \;\xrightarrow{\;\rho\;}\; \underbrace{w_{ij}}_{d\text{차원 가중치}}$$

> $\gamma$가 단순 linear가 아니라 MLP인 이유: 뺄셈만으로는 채널 간 상호작용이 전혀 없다. $\gamma$가 채널들을 섞어주는 역할을 맡는다.

---

## 3. ⚠️ Softmax는 어느 방향으로 걸리는가

여기가 논문만 읽으면 반드시 막히는 지점이다. **논문 본문은 "$\rho$ is a normalization function such as softmax"라고만 쓰고 축을 명시하지 않는다.** 수식 표기도 $\rho(\cdot)$가 $\sum$ 안에 들어가 있어서, 마치 이웃 $j$ 하나만 보고 계산하는 것처럼 보인다. 이건 표기의 생략일 뿐이다.

### 정답: 이웃(neighbor) 축으로 걸린다. 채널마다 독립적으로.

점 $i$의 이웃이 $k$개라면, $\gamma$의 출력을 전부 모으면 **$k \times d$ 행렬**이 된다.

```
              ch1    ch2    ch3   ...  (채널 d개, 가로)
  이웃 j=1 [  2.0    0.0    1.0  ... ]
  이웃 j=2 [  0.0    2.0    1.0  ... ]
  이웃 j=3 [  ...                    ]
   (세로, k개)
```

Softmax는 이 행렬을 **세로 방향(열마다)** 으로 정규화한다.

$$\sum_{j \in \chi(i)} w_{ij}^{(c)} = 1 \qquad \text{모든 채널 } c \text{에 대해}$$

즉 **채널이 $d$개면 softmax를 $d$번 따로 돌리는 것**이다. 각각은 "$k$개 이웃 중 누구를 볼까"를 정한다.

### 왜 이 방향이어야 하는가 (근거 3가지)

**(1) 그래야 가중 평균이 된다.** 어텐션의 존재 이유는 "이웃들을 적절한 비율로 섞기"다. 비율이 되려면 합이 1이어야 하고, 그 합은 당연히 **섞는 대상인 이웃들**에 대한 합이어야 한다. Scalar attention에서 softmax가 $j$에 대해 걸리는 것과 완전히 동일한 논리다. Vector attention은 그걸 채널별로 $d$번 반복할 뿐이다.

**(2) 채널 방향으로 걸면 망가진다.** 만약 각 이웃 안에서 채널들끼리 softmax를 하면:
- 채널들이 **서로 경쟁**하게 된다. ch1이 커지면 ch2가 강제로 작아진다. 이건 아무 의미 없는 커플링이다.
- 이웃 축에는 정규화가 없으므로, 이웃 개수 $k$가 커질수록 $y_i$의 크기가 그냥 커진다. kNN 개수가 바뀌면 스케일이 터진다.
- 무엇보다 **"어텐션"이 아니게 된다.** 어떤 이웃도 걸러지지 않고 전부 기여한다.

**(3) 구현이 그렇게 되어 있다.** 공식 구현(및 Pointcept의 `PointTransformerLayer`)에서 어텐션 텐서의 shape은 `(n, nsample, c)` = (점 개수, 이웃 개수, 채널)이고, softmax는 **`dim=1`** 즉 `nsample` 축에 적용된다.

---

## 4. 숫자로 보기

채널 3개($d=3$), 이웃 2개($k=2$)인 장난감 예시.

**Step 1.** $\gamma$가 뱉은 raw score ($k \times d$):

|  | ch1 | ch2 | ch3 |
|---|---|---|---|
| 이웃 1 | 2.0 | 0.0 | 1.0 |
| 이웃 2 | 0.0 | 2.0 | 1.0 |

**Step 2.** 세로(이웃 축)로 softmax:

|  | ch1 | ch2 | ch3 |
|---|---|---|---|
| 이웃 1 | **0.88** | 0.12 | 0.5 |
| 이웃 2 | 0.12 | **0.88** | 0.5 |
| *합* | *1.0* | *1.0* | *1.0* |

**Step 3.** Value가 $\alpha(x_1) = (10,\ 20,\ 30)$, $\alpha(x_2) = (40,\ 50,\ 60)$ 이라면:

$$
\begin{aligned}
y^{(1)} &= 0.88\times 10 + 0.12 \times 40 = 13.6 \quad \text{(이웃 1에서 거의 다 가져옴)}\
y^{(2)} &= 0.12\times 20 + 0.88 \times 50 = 46.4 \quad \text{(이웃 2에서 거의 다 가져옴)}\
y^{(3)} &= 0.5\ \times 30 + 0.5\ \times 60 = 45.0 \quad \text{(반반 평균)}
\end{aligned}
$$

$$\mathbf{y}_i = (13.6,\ 46.4,\ 45.0)$$

**같은 점 $i$인데 채널 1은 왼쪽 이웃을, 채널 2는 오른쪽 이웃을 본다.** 이게 vector attention이 하는 일의 전부다. Scalar attention이었다면 세 채널 모두 동일한 비율(예: 0.5/0.5)로 섞여서 $(25, 35, 45)$가 나왔을 것이다.

---

## 5. 그래서 Output $\mathbf{y}_i$ 는 무엇인가

**형태**: 입력과 똑같은 $d$차원 벡터. 점 하나당 하나. 점 개수도 안 변한다. 이 층은 feature를 **정제**할 뿐 shape을 바꾸지 않는다.

**의미**: 세 가지 표현으로 같은 걸 말하면,

1. **채널별로 다른 이웃 가중 평균.** $y_i$의 각 성분은 그 채널만의 독립적인 convex combination 결과다.
2. **이웃을 고르는 게 아니라 재조립하는 것.** Scalar attention이 "이웃 A와 C를 채택"이라면, vector attention은 "A에서 기하 채널을, C에서 색 채널을 가져와 새 feature를 조립"이다.
3. **주변 점들로부터 부분부분 정보를 취합해 갱신된, 점 $i$의 새로운 설명.**

---

## 6. 다른 관점: 이건 사실 동적 Convolution이다

일반 convolution은 이렇게 생겼다.

$$y_i = \sum_j W_j \odot x_j$$

여기서 $W_j$는 **학습으로 고정된** 채널별 가중치이고, $j$는 격자 위의 정해진 위치(왼쪽 위, 오른쪽 아래...)다. 주목할 점: **conv도 원래 채널마다 가중치가 다르다.**

Point cloud에는 격자가 없어서 "왼쪽 위 이웃"을 정의할 수 없다. 그래서 $W_j$를 미리 만들어둘 수 없다. Vector attention은 이걸 **그 자리에서 생성**한다.

$$W_{ij} = \rho\big(\gamma(\varphi(x_i) - \psi(x_j) + \delta_{ij})\big)$$

- $\delta_{ij} = \theta(p_i - p_j)$ 덕에 **상대 위치**에 의존 → conv의 "커널 위치" 역할을 대체
- $\varphi(x_i) - \psi(x_j)$ 덕에 **내용**에도 의존 → conv에는 없는 추가 능력

이 관점에서 보면 vector attention은 자연스럽고, 오히려 **scalar attention이 "채널 방향으로 전부 묶인 이상한 conv"** 로 보인다.

---

## 7. Multi-head Attention과의 관계

가중치 하나가 몇 개 채널을 담당하는지(**granularity**)로 줄을 세우면:

| 방식 | 가중치 1개가 커버하는 채널 수 | 점 $i$당 어텐션 모양 |
|---|---|---|
| Scalar attention | $d$ (전부) | $k$ |
| Multi-head ($h$개 head) | $d/h$ | $k \times h$ |
| **Vector attention** | **1** | $k \times d$ |

이 스펙트럼에서 **vector attention은 $h = d$인 극단**에 해당한다. 다만 아래 단서가 중요하다.

> ⚠️ **가중치를 만드는 방식은 다르다.** $h=d$인 multi-head는 각 head의 query/key가 1차원이 되어 내적이 그냥 스칼라 곱으로 퇴화한다(표현력 붕괴). Vector attention은 내적을 **아예 버리고** 뺄셈 + MLP로 관계를 계산하므로, 채널 간 상호작용이 $\gamma$ 안에서 유지된다. 따라서 "$h=d$인 multi-head"는 **비유이지 등가가 아니다.**

---

## 8. Point Transformer에서의 최종 형태

논문 Eq. 2(위에서 다룬 일반형)와 Eq. 3(Point Transformer layer)은 **다르다.** 두 가지가 바뀐다.

$$y_i=\sum_{x_j\in \chi(i)}\rho\big(\gamma(\varphi(x_i)-\psi(x_j)+\delta)\big)\odot \big(\alpha(x_j)+\delta\big)$$

1. **$\mathcal{X} \to \chi(i)$**: 전체 점이 아니라 **kNN 이웃**으로 제한. 점이 수만 개라 전역 어텐션은 계산량이 감당 안 된다. → local attention.
2. **$\alpha(x_j) + \delta$**: position encoding을 **value에도** 더한다. $\delta$가 어텐션 계산용과 value 보정용으로 **두 번, 다른 역할로** 등장한다. Ablation상 둘 다 넣는 게 가장 좋았다.

즉 위치 정보 $p$가 들어오는 통로는 ① kNN으로 이웃을 고를 때 ② $\delta = \theta(p_i - p_j)$ 두 개다.

또한 이 layer는 단독으로 쓰이지 않고 residual block 안에 들어간다.

$$x \to \text{linear} \to \text{PT layer} \to \text{linear} \to (+\,x)$$

따라서 $y_i$는 블록의 최종 출력이 아니라 **residual branch의 출력**이다.

---

## 9. 후속 연구: Grouped Vector Attention (PTv2)

채널마다 **완전히** 독립적인 가중치는 파라미터가 과하고 과적합을 부른다. PTv2는 채널을 그룹으로 묶어 그룹 안에서 가중치를 공유하는 *grouped vector attention*을 쓴다. 위 7번 표의 **중간 지대로 의도적으로 후퇴**한 셈이다.

$$\text{scalar} \;\longleftrightarrow\; \text{grouped (PTv2)} \;\longleftrightarrow\; \text{vector (PTv1)}$$

---

## 요약

- Vector attention = 이웃당 가중치가 **벡터**. 채널마다 다른 이웃을 볼 수 있다.
- 가능한 이유는 $\beta$(뺄셈)가 내적과 달리 **차원을 유지**하기 때문.
- Softmax는 **이웃 축**으로, **채널마다 독립적으로** 걸린다. (논문 본문엔 명시 없음, 구현으로 확인)
- Output은 입력과 같은 $d$차원 벡터이되, 각 채널이 서로 다른 이웃 조합으로 만들어진 값.
- 관점을 바꾸면 **content-adaptive continuous convolution**.
