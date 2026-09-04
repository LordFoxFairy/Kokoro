---
layout: home

hero:
  name: Kokoro Developer
  text: Build durable agent workflows
  tagline: A contract-first guide to asynchronous runs, resumable AG-UI streams, and product resources.
  actions:
    - theme: brand
      text: Start the quickstart
      link: /quickstart
    - theme: alt
      text: Browse API v1
      link: /reference/v1/
---

<section class="protocol-strip" aria-label="Kokoro run protocol">
  <article class="protocol-step">
    <span>01 / ADMIT</span>
    <h2>Submit once</h2>
    <p>Use a stable idempotency key and receive an asynchronous run receipt.</p>
  </article>
  <article class="protocol-step">
    <span>02 / FOLLOW</span>
    <h2>Read AG-UI</h2>
    <p>Consume committed event frames and retain the latest opaque cursor.</p>
  </article>
  <article class="protocol-step">
    <span>03 / RESUME</span>
    <h2>Continue exactly</h2>
    <p>Reconnect strictly after the last confirmed frame without inventing offsets.</p>
  </article>
</section>

## One contract, one reference

The public reference is rebuilt from the pinned `kokoro-bff` OpenAPI on every portal build. Guides explain workflows; the owner contract remains the only field-level source of truth.

[Understand the API boundary →](/introduction)
