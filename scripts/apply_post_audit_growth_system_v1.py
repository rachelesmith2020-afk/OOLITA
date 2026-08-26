#!/usr/bin/env python3
"""Compatibility entry point for the post-audit OOLITA growth system."""

# The final consistency workflow imports this v1 name. Keep that stable while
# the resilient implementation lives in v2.
import apply_post_audit_growth_system_v2  # noqa: F401,E402
