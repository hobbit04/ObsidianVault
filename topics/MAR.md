---
tags:
  - ComputerVision
---
**Title: Autoregressive Image Generation without Vector Quantization**
## Introduction
---
지금까지 Autoregressive은 다 이산적인 공간에서만 연구가 진행 됐었음.. 하지만 AR의 본질은 "이전 토큰들로부터 다음 토큰을 예측하는" 것이므로, per-token probability distribution을 디퓨전으로 모델링 하면 연속 공간에서도 사용할 수 있다!
> 연속 공간에서의 디퓨전 과정 -> 토큰 당 확률 분포를 모델링

디퓨전에서 condition으로 사용될 벡터 $z$를 autoregressive 모델이 생성함.

Diffusion loss 라는 것을 새로 정의 했음. AR, MAR 등에서 효과적임을 실험으로 보여줌. 

## Related Work
---
**GIVT: Generative Image-to-Vector Transformer**
> 큰 구조에서는 유사함.. GIVT에서는 토큰의 분포가 미리 정해진 Gaussian mixture model로 나타나는데, 표현력이 부족할 수 있다(Mixture의 개수를 K로 미리 정하기 때문). 
> 공통점: 연속공간 상의 벡터를 AR로 만든다. 
> 차이점: GIST는 Gaussian mixture model을, MAR은 Diffusion을 이용해 확률 분포를 만들어 낸다.

**Diffusion for Representation Learning**
>원래 diffusion은 노이즈를 만들고 제거하는 과정을 학습해 이미지 생성에 사용됨. 하지만 추가적으로 representation learning에도 이용 될 수 있는데, 대표적으로 Masked AutoEncoder의 손실함수를 L2 loss에서 denoising diffusion decoder로 대체한 DiffMAE가 있다. 

**Diffusion for Policy Learning**
> Diffusion을 이용해 로봇의 행동 정책을 만드는 방법. 가능한 actions 중에서 선택하는 과정이 robot observations를 denoising 하는 과정을 통해 일어난다. 
## Method
---
### Rethinking Discrete-Valued Tokens
기존의 이산적인 공간에서의 토큰을 사용하는 autoregressive 모델을 생각해보자. 다음 위치에 와야할 토큰이 $x$(Ground truth token)라고 하면, $x$는 이산적인 토큰이기 때문에 $0\leq x<K$로 표현할 수 있다. 즉 어떤 정수(인덱스)를 나타내게 된다. $K$를 vocabulary size 라고 한다. 트랜스포머 등의 모델에서는 디코더만 사용하는데, 이때 디코더는 $D$ 차원의 벡터 $z$를 내놓는다. 이를 K-way classifier matrix $W \in \mathbb{R}^{K \times D}$ 에 곱하여 K 차원의 벡터를 구한다. 여기에 softmax를 취하면 Categorical probability distribution 을 만들 수 있다. 즉, $$p(x|z)=\text{softmax}(Wz)$$이 $z$를 condition으로 할 때 다음 토큰 $x$에 대한 확률 분포이다.

1. 이 확률분포와 실제 확률 분포의 차이를 구할 수 있어야 한다. 즉 이 목적의 손실함수가 필요. Categorical 에선 one hot vector 와 cross entropy loss를 구해 알 수 있음. 
2. 해당 확률 분포에서 샘플링을 할 수 있는 sampler가 필요. (Categorical distribution에서는 Gumbel-max method나 inverse transform sampling으로 샘플링 가능)

결론적으로, 꼭 토큰이 discrete 할 필요는 없다.
### Diffusion Loss
$$\mathcal{L}(z,x)=\mathbb{E}_{\epsilon, t}[||\epsilon - \epsilon_\theta (x_t|t, z)||^2]$$
$\epsilon$: Noise vector, sampled from $\mathcal{N}(0, I)$.
$x_t$: Noise-corrupted vector. t에 따라 노이즈 양이 바뀜. 점점 노이즈가 늘어나는.
이 식은 일종의 score matching으로 작용한다. 
$\epsilon_\theta$: MLP 네트워크로 $x_t$를 입력 받으며 $t, z$를 조건으로 사용한다. Noise estimator 역할을 한다.

즉 실제 노이즈와 $x_t$를 이용해 추정한 노이즈의 MSE이다. 

>연속 공간의 token $x$를 예측하기 위해 설계된 diffusion 기반의 손실 함수

 Sampling은 reverse diffusion 과정으로 진행함. 즉 $x_t$에서 $x_{t-1}$를 만드는 과정이다. (노이즈 제거 방향)
$$x_{t-1}=\frac{1}{\sqrt{\alpha_t}}(x_t-\frac{1-\alpha_t}{\sqrt{1-\bar{\alpha_t}}}\epsilon_\theta(x_t|t, z)) + \sigma_t\delta$$
 - 첫 번째 항: 노이즈 제거 및 분산 보정. $\epsilon_\theta$가 $x_t$에 얼마나 많은 노이즈가 있었는지를 예측하고, 이를 제거하는 형태의 식이다.
 - 두 번째 항: Sampling에 무작위성을 추가하기 위함.
 좋은 성능을 내기 위해서는 Temperature 항이 필요하기에 sampling시 $\sigma_t \delta$에 $\tau$를 곱한다. 
### Diffusion Loss for AR models
Autoregressive model을 수식으로 표현하면 다음과 같다. $$p(x^1, ...,x^n)= \prod_{i=1}^np(x^i|x^1,...,x^{i-1}) $$여기서 우변의 식을 $z^i=f(x^1,...,x^{i-1})$를 이용해 $p(x^i|z^i)$로 바꿀 수 있다. 이 식은 diffusion loss를 적용할 수 있어서 $f(\cdot)$까지 학습할 수 있다.
### Unifying AR and Masked Generative Models
Autoregression 이라는 개념 자체는 신경망의 구조와는 상관이 없다. 보통 Transformer를 이용해 구현할 때, AR은 causal attention을 사용하게 된다. 주로 자연어처리처럼 순서가 곧 인과관계가 되는 task를 다루기 때문인데, 양 방향 attention으로도 구현할 수 있음을 이 논문에서는 보인다. AR은 이전 토큰들로 다음 토큰을 예측하는 것을 목표로 하지, 이전 토큰들이 서로 어떻게 연결되어 있는지(attention)는 상관하지 않는다. 
![[Pasted image 20250709161322.png]]
cf. MAE: Masked AutoEncoder. 이미지를 패치로 나누어 일부 패치를 masking 한다. `[m]`으로 대체. 그리고 마스킹 되지 않은 패치들을 encoder의 입력으로 넣어 latent vector를 뽑아낸 다음 decoder가 마스킹 된 위치를 채우도록 학습한다. 여기서는 마스킹을 하나의 토큰에 대해서만 처리하고 attention을 모든 unmasked 토큰에 대해 연결했다. --> full attention

Tradeoffs: KV-cache를 쓸 수 없음. 대신 여러 토큰을 한번에 생성함으로써 steps 수를 줄일 수 있음.

![[Pasted image 20250705134059.png]]
**Masked autoregressive models**
기존의 masked generative modeling(e.g., MAE)에서는 무작위 토큰들을 known/predicted 토큰들을 이용해 예측했다. 이는 토큰의 순서를 무작위로 바꾸고, 앞의 토큰들을 이용해 뒤의 토큰들을 예측하는 식으로 구현할 수 있다(figure 3(c)). --> 이것도 Autoregressive 과정임! 다만 하나씩 예측하는게 아닐 뿐.
$$p(x^1, ...,x^n)=p(X^1,...,X^K)=\prod_k^Kp(X^k|X^1, ...,X^{k-1})$$
## Implementaion
---
### Diffusion Loss
- Noise scheduler: Cosine shape, 1000 steps for training and 100 steps for inference
- Diffusion Loss는 자연적으로 CFG를 지원한다. 
- Denoising을 위해서는 MLP with a few residual blocks을 사용. 
### AR and MAR Image Generation
- Tokenizer: LDM의 VQ-16 and KL-16 버전 사용. 각각 이산 공간의 토큰과 연속 공간의 토큰을 만들어내며, 이 둘을 비교하기 위함임.
- Transformer: ViT의 모델을 사용함. 
- Autoregressive baseline: GPT의 causal attention을 사용함. 어텐션 matrix에 triangular masking을 적용함. Inference시 temperature sampling과 kv-cache를 사용함. 
- MAR models: Bidirectional attention을 사용. 학습 시 70% 또는 100% 마스킹을 함. 대신 항상 64개의 `[cls]` tokens를 추가함. 추론 시 마스킹 비율을 1.0에서 0으로 코사인 스케줄링 하며, 매 step마다 일부를 예측함. 총 64 steps에 걸쳐 추론을 완료. 
## Experiments
---
- Dataset: ImageNet. 256 x 256
- Metrics: FID, IS
- Tokenizers: 위에서 말했듯, VQ-16과 KL-16을 이용.
### Properties of Diffusion Loss
![[Pasted image 20250705141256.png]]
Diffusion loss(KL-16 tokenizer)를 이용해 학습한 모델이 FID와 IS 에서 더 좋은 점수를 내는 것을 확인할 수 있다.
이유 분석: 연속 공간의 tokenizer가 정보 손실이 더 적음. & diffusion 과정이 categorical 모델모다 실제 분포를 더 잘 나타냄

![[Pasted image 20250709171321.png]]
Diffusion loss의 또 다른 장점은 여러 tokenizer를 사용할 수 있다는 것이다. VQ-16 같은 이산 공간의 tokenizer를 이용할 수도 있다! 유한한 표현으로 매핑되기 직전의 연속 공간의 벡터를 token으로 사용하면 된다. 그렇게 했더니 FID 성능이 8.79에서 7.82로 더 좋아졌다. --> Diffusion 방식이 더 성능이 좋다는 근거
(cf. rFID: 복원된 이미지가 원본과 얼마나 유사한가)
KL-8: mismatch
Consistency: Consistency Decoder. A non-VQ tokenizer of a different architecture/stride designed for different goals.
맨 밑의 KL-16: ImageNet으로 학습한 tokenizer. Original은 OpenImages에서 학습 됐음.

![[Pasted image 20250709232004.png]]
Diffusion을 수행하는 small MLP의 크기를 바꿔가면서 진행한 실험. 기본은 width가 1024인 MLP이지만 2M의 파라미터로도 충분히 좋은 성능을 보인다.

![[Pasted image 20250709232214.png]]
DDPM에서 하는 것처럼, 1000step noise schedule을 이용해 학습하지만 추론시 더 적은 step을 이용한다. 그래프를 보면 100 steps 정도면 더 많이 해도 성능 향상이 없다는 것을 알 수 있다.

![[Pasted image 20250709232332.png]]
Cross-entropy loss를 사용할 때처럼, temperature가 중요한 영향을 미친다. 
### Properties of Generalized AR models
1. Raster order -> Random order 이 높은 성능 향상을 보였음. 
2. Causal attention -> bidirectional attention 또한 성능 향상으로 이어짐
**Random order & bidirectional AR = MAR that predicts one token at a time**

![[Pasted image 20250709232739.png]]
한번에 여러 토큰을 생성하기 때문에 더 빠르지만, 정확도와 trade-off가 존재한다. AR steps 수를 바꿔가며 plot을 나타냈고 MAR이 가장 좋은 speed/accuracy trade-off를 보였다. 
왜 지수함수 꼴로 감소하냐: step이 증가하면 이미지를 더 잘게 쪼개나..? 

## Appendix
---
### Limitations and Broader Impacts
1. Can produce images with noticeable artifacts
2. Relies on existing pre-trained tokenizers(e.g., VQ-16. KL-16)
3. Resources were limited. Only tested on the ImageNet benchmark. 

## Limitations and Questions
---
1. 256 x 256 images로만 실험 -> 더 많은 픽셀에서도 bidirectional attention이 좋은 speed/accuracy trade-off를 보일까? 해상도 높아짐에 따라 성능이 유지되려면 모델의 크기가 어떻게 증가할지 궁금함.
2. ImageNet에서 tokenizer와 AR, diffusion model을 학습한 결과가 tokenizer를 OpenImage에서 학습한 것보다 좋았는데, 그 이유가 같은 데이터셋에서 학습했기 때문일 수도 있지 않을까? AR, diffusion model 학습을 OpenImage에서 하고 tokenizer도 OpenImage에서 학습한 결과를 비교하고 싶다.
3. 