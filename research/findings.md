# Findings

- Mixed sampling + graph compatibility overlaps SonicSampler; log-normalizers overlap FlashSampling
  and vLLM. The original broad novelty claim has been narrowed before implementation.
- A finite candidate budget is distinct from a user top-k setting. Certify against the full target
  mass, never against a candidate-only renormalization.
- Sparse recovery may save bytes without releasing the engine batch barrier. Keep these claims separate.
- A rational mass oracle can prove its own finite reference results exactly, but cannot qualify
  floating-point exp/logsumexp, real collectives, RNG integration, graph execution or model accuracy.
- Target: OSDI ’27 preliminary CFP; 2026-12-01 abstract and 12-08 full paper, both 22:59 UTC.
