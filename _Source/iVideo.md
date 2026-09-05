---
tags:
  - ComputerVision
---
**Title: Interactive VideoGPTs are ScalableWorld Models**

*Topics to study more*
- World models
- Model based RL: model free rl 과 반대되는 개념으로, 주로 planning을 다룬다. 주어진 environment를 정확히 구현한 다음에 보상을 최대화 시키는 방식. 
- Partially observable MDP
- VQGAN: Vector Quantized Variational Autoencoder와 Generative Adversarial Network를 결합한 구조. 트랜스포머 모델과 결합하면 좋은 성능을 보임. VQ-VAE로 이미지를 토큰 시퀀스처럼 처리. 이후 GAN을 통해 이미지의 품질 개선.
- VQ-VAE: 이미지를 토큰으로 생각하는 방식의 VAE. 
- $L_1$ reconstruction loss
- Commitment loss
- Perceptual loss
- Adversarial loss
- RMSNorm
- SwiGLU
- Rotary positional embeddings

## Notes
---
AR transformer 프레임 워크를 만들어 멀티 모달 신호를 처리할 수 있다. Diffusion 안씀!
SOTA 모델은 아니지만 경쟁력 있는 성능을 보인다.
Interactivity와 scalability 는 일종의 trade off가 있는 듯..?
Interactivity는 autoregressive 방식으로 챙길 수 있고, scalability는 압축적인 tokenization을 이용해 얻을 수 있는 것 같다,,

## Problem Formulation
---
World model은 POMDP로 모델 되는데, state $s_t$의 일부만을 알 수 있는 MDP이다. $o_t$가 관측한 state을 의미하게 되고, 식으로는 $o_t=\phi(s_t$) 로 나타낼 수 있다. 

연속적인 프레임 몇 장을 주면 다음 state를 예측할 수 있어야 한다. 

## Interactive VideoGPT
---
이 모델은 두 가지 부분으로 구성되어 있다.
1. Compressive tokenizer: Autoregression에서 사용되는 토큰을 이용해 동영상 프레임을 이산화 시키는 부분
2. Autoregressive transformer: 다음 토큰을 예측하는 부분

Pre-traing은 상식적인 움직임들과 상호작용을 배우기 위해 필요하고, human and robotic manipulation 동영상들을 이용해 학습한다. 
### Compressive tokenization
두 개의 encoder-decoder 쌍으로 이루어진 Conditional VQGAN을 이용해 video를 토큰화 시킨다. 이 방식이 새로운 접근임.
![[Pasted image 20250702175528.png|600]]
Video data는 시공간적으로 중복되는 정보가 많다. 따라서 매 프레임 전체를 처리하는 것이 아니라 의미 있는 정보들만 요약한 토큰들로 구성해 transformer의 입력으로 사용하는 방법을 택한다. 또한 context를 condition으로 한다. 
![[Pasted image 20250702203131.png]]
왼쪽 항은 처음 몇 프레임을 의미하며, 이는 중요하므로(덜 redundant) 전부 그대로 토큰화 된다. 
### Interactive prediction with Transformers
토큰화 --> flattened into a sequence of tokens
### Pre-Training
Cross-entropy loss를 사용해서 다음 비디오 토큰을 예측하도록 pre-train 시켰다. 
이때 사용한 데이터는,
1. Open X-Embodiment
2. Something-Something v2
데이터 셋이었다. 
### Fine-Tuning

## Experiments
---
**Metrics used;**
1. FVD
2. PSNR
3. SSIM
4. LPIPS


## Limitations and Questions
---
1. Pre training 과정이 있어야 해서, pre train을 시킨 환경과 많이 다른 환경에서는 잘 작동하지 않을 것 같다.
2. 논문에서도 언급 됐듯이, pre train에 사용한 데이터 셋이 2개로 조금 부족하다. 심지어 겹치는 것도 있어서 연구진이 일일이 확인한 것으로 보인다.
3. 토큰을 flatten 한다음에 Transformer의 입력으로 넣었는데, transformer 기반의 다양한 모델들에도 시도해보면 어떨까..? (ChatGPT의 제안: TimeSformer, TokenLearner, etc,.)