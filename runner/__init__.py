"""``runner`` — Phase 1 execution/orchestration package.

Hosts the agent-run glue (:mod:`runner.authoring`) that assembles a single per-run
authoring invocation from the already-built Phase 1 pieces (spec loader, target
config, MCP config, QA system prompt, Planner/Generator sub-agents) and drives it
through an injectable agent runner. See ``runner/README.md``.
"""
