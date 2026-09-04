# Introduction

Kokoro API v1 is the public Product API contract owned by `kokoro-bff`. It exposes projects, chat sessions, asynchronous Agent runs, scheduled tasks, library projections, and supporting product resources through one versioned HTTP surface.

The portal composes guides and generated reference material. It does not own or copy the API schema. Every reference page is generated from the pinned canonical OpenAPI artifact in the BFF repository.

## Current contract status

Version `1.0.0` is marked **beta**. An operation appearing in the contract describes its public wire shape; it does not by itself prove that every live adapter, persistence path, or service-level objective is complete.

Continue with the [quickstart](./quickstart) or inspect the [v1 reference](./reference/v1/).
