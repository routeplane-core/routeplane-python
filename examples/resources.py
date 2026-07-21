"""The non-OpenAI gateway surfaces — status, logs, FinOps, prompt management, and
cache — hang off the ``Routeplane`` client as resource namespaces.

    pip install routeplane
    python examples/resources.py
"""

from routeplane import Routeplane

rp = Routeplane(api_key="rp_live_...")

# Check gateway health
status = rp.status.retrieve()
print(f"Gateway: {status}")

# View recent logs
logs = rp.logs.list(limit=10)
print(f"Recent requests: {len(logs)}")

# FinOps usage
usage = rp.finops.usage()
print(f"Usage: {usage}")

# Prompt management
rendered = rp.prompts.render("welcome-v2", variables={"name": "Rohit"})
print(f"Rendered: {rendered}")

# Purge cache
rp.cache.purge()
print("Cache purged")
