"""
Sequence Generator — converts action template descriptors into finalized JSON action sequences.

Key operations:
1. Resolve parameter values from realistic ranges/lists in api_functions.py
2. Resolve {{steps[N].output.<key>}} variable references by cross-referencing output_refs
3. Add conditional branches for rollback steps (condition: "on_failure", triggers_from)
4. Inject dependency edges based on depends_on fields
5. Assign step numbers (1-indexed)
6. Generate variable_chain tracing map
7. Generate rollback action steps as separate actions
8. Compute complexity score

Usage:
    from sequence_generator import build_sequence
    import random
    rng = random.Random(42)
    result = build_sequence(template_dict, rng)
"""

import random
import re
from api_functions import API_FUNCTIONS


def _build_api_lookup():
    """Build a lookup dict: (namespace, function) -> API function definition."""
    lookup = {}
    for f in API_FUNCTIONS:
        lookup[(f["namespace"], f["function"])] = f
    return lookup


API_LOOKUP = _build_api_lookup()


def _get_param_values(api_fn):
    """Extract possible parameter values from an API function definition."""
    param_values = {}
    if not api_fn:
        return param_values
    for p in api_fn.get("params", []):
        name = p["name"]
        values = p.get("values", [])
        ptype = p.get("type", "string")
        if values:
            param_values[name] = {"values": values, "type": ptype}
        else:
            # Empty values list means dynamic (e.g., instance_id from output)
            param_values[name] = {"values": [], "type": ptype, "dynamic": True}
    return param_values


def _resolve_placeholder(key, params_dict, rng, param_values):
    """Resolve a {placeholder} to a concrete value."""
    # Check if it's already in params_dict (e.g., from parent template)
    if key in params_dict:
        val = params_dict[key]
        # If it's a boolean or integer, return as-is
        if isinstance(val, (bool, int, float)):
            return val
        return str(val)

    # Look up possible values from the parameter schema
    if key in param_values:
        info = param_values[key]
        choices = info.get("values", [])
        if choices:
            return rng.choice(choices)
        # If no values defined, return a synthetic value based on type
        ptype = info.get("type", "string")
        if ptype == "integer":
            return rng.randint(1, 100)
        elif ptype == "boolean":
            return rng.choice([True, False])
        else:
            return f"{key}-{rng.randint(100, 999)}"

    # Unknown key — return a synthetic value
    return f"{key}-{rng.randint(100, 999)}"


def _resolve_params(action_params, params_dict, rng, prior_outputs, param_values_for_action):
    """Resolve all parameter values in an action's params dict.
    
    Handles:
    - {placeholder} -> concrete value from params_dict or random selection
    - {{steps[N].output.<key>}} -> prior step output value
    """
    resolved = {}
    for pname, pvalue in action_params.items():
        if isinstance(pvalue, str):
            # Check for variable references: {{steps[N].output.<key>}}
            var_match = re.match(r'\{\{steps\[(\d+)\]\.output\.(\w+)\}\}', pvalue)
            if var_match:
                step_idx = int(var_match.group(1))
                output_key = var_match.group(2)
                # This should already be validated before being called
                if step_idx in prior_outputs and output_key in prior_outputs[step_idx]:
                    resolved[pname] = prior_outputs[step_idx][output_key]
                else:
                    # Fallback — shouldn't happen if validation is correct
                    resolved[pname] = f"ref-{step_idx}-{output_key}"
            else:
                # Simple placeholder: {placeholder_name}
                ph_match = re.match(r'\{(\w+)\}', pvalue)
                if ph_match:
                    key = ph_match.group(1)
                    resolved[pname] = _resolve_placeholder(key, params_dict, rng, param_values_for_action)
                else:
                    resolved[pname] = pvalue
        elif isinstance(pvalue, (bool, int, float)):
            resolved[pname] = pvalue
        elif isinstance(pvalue, list):
            resolved[pname] = [_resolve_placeholder(str(v), params_dict, rng, param_values_for_action) if isinstance(v, str) and v.startswith("{") else v for v in pvalue]
        elif isinstance(pvalue, dict):
            resolved[pname] = {k: _resolve_placeholder(str(v), params_dict, rng, param_values_for_action) if isinstance(v, str) and v.startswith("{") else v for k, v in pvalue.items()}
        else:
            resolved[pname] = str(pvalue)
    return resolved


def _generate_output_values(output_refs, api_fn, resolved_params, rng):
    """Generate realistic output values based on the function's output_fields."""
    output_values = {}
    if not output_refs or not api_fn:
        return output_values

    output_fields = api_fn.get("output_fields", {})

    for key, description in output_refs.items():
        desc = description or output_fields.get(key, "")
        desc_lower = desc.lower()

        if "id" in key.lower() or key.endswith("_id") or key.endswith("_uid"):
            if "instance" in desc_lower:
                output_values[key] = f"i-{rng.randint(1000000, 9999999)}"
            elif "security" in desc_lower or "group" in desc_lower:
                output_values[key] = f"sg-{rng.randint(10000000, 99999999)}"
            elif "subnet" in desc_lower:
                output_values[key] = f"subnet-{rng.choice(['abc123', 'def456', 'ghi789'])}"
            elif "bucket" in desc_lower:
                output_values[key] = f"bucket-{rng.randint(1000, 9999)}"
            elif "alert" in desc_lower:
                output_values[key] = f"alert-{rng.randint(1000, 9999)}"
            elif "build" in desc_lower:
                output_values[key] = f"build-{rng.randint(10000, 99999)}"
            elif "ticket" in desc_lower:
                output_values[key] = f"TKT-{rng.randint(1000, 9999)}"
            elif "lead" in desc_lower:
                output_values[key] = f"lead-{rng.randint(1000, 9999)}"
            elif "opportunity" in desc_lower:
                output_values[key] = f"opp-{rng.randint(1000, 9999)}"
            elif "campaign" in desc_lower:
                output_values[key] = f"camp-{rng.randint(1000, 9999)}"
            elif "payment" in desc_lower:
                output_values[key] = f"pay_{rng.randint(100000, 999999)}"
            elif "invoice" in desc_lower:
                output_values[key] = f"inv_{rng.randint(100000, 999999)}"
            elif "account" in desc_lower:
                output_values[key] = f"acct_{rng.randint(10000, 99999)}"
            elif "employee" in desc_lower or "profile" in desc_lower:
                output_values[key] = f"emp-{rng.randint(1000, 9999)}"
            elif "pipeline" in desc_lower:
                output_values[key] = f"pl-{rng.randint(1000, 9999)}"
            elif "kubernetes" in desc_lower or "k8s" in desc_lower:
                output_values[key] = f"ns-{rng.randint(1000, 9999)}"
            elif "review" in desc_lower or "cycle" in desc_lower:
                output_values[key] = f"rev-{rng.randint(1000, 9999)}"
            elif "leave" in desc_lower:
                output_values[key] = f"lv-{rng.randint(1000, 9999)}"
            elif "posting" in desc_lower:
                output_values[key] = f"job-{rng.randint(1000, 9999)}"
            elif "interview" in desc_lower:
                output_values[key] = f"int-{rng.randint(1000, 9999)}"
            elif "module" in desc_lower or "training" in desc_lower:
                output_values[key] = f"mod-{rng.randint(1000, 9999)}"
            elif "enrollment" in desc_lower:
                output_values[key] = f"enr-{rng.randint(1000, 9999)}"
            elif "person" in desc_lower or "user" in desc_lower:
                output_values[key] = f"usr-{rng.randint(10000, 99999)}"
            elif "promotion" in desc_lower:
                output_values[key] = f"promo-{rng.randint(1000, 9999)}"
            elif "artifact" in desc_lower:
                output_values[key] = f"artf-{rng.randint(1000, 9999)}"
            elif "dashboard" in desc_lower:
                output_values[key] = f"dash-{rng.randint(1000, 9999)}"
            else:
                output_values[key] = f"id-{rng.randint(100000, 999999)}"

        elif "ip" in key.lower() or "public_ip" in key.lower():
            output_values[key] = f"{rng.randint(10, 200)}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"
        elif "private_ip" in key.lower():
            output_values[key] = f"10.0.{rng.randint(0, 255)}.{rng.randint(1, 254)}"
        elif "state" in key.lower() or "status" in key.lower():
            output_values[key] = rng.choice(["running", "active", "completed", "pending", "available"])
        elif "arn" in key.lower():
            output_values[key] = f"arn:aws:{rng.choice(['ec2', 's3', 'lambda', 'rds'])}:us-east-1:{rng.randint(100000000000, 999999999999)}:{rng.choice(['instance', 'bucket', 'function'])}/{rng.choice(['prod', 'staging', 'dev'])}-{rng.randint(100, 999)}"
        elif "url" in key.lower() or "link" in key.lower() or "download" in key.lower():
            output_values[key] = f"https://{rng.choice(['api', 'console', 'app'])}.example.com/{rng.choice(['resources', 'dashboard', 'reports'])}/{rng.randint(1000, 9999)}"
        elif "email" in key.lower():
            output_values[key] = f"{rng.choice(['user', 'admin', 'contact', 'support'])}{rng.randint(1, 999)}@example.com"
        elif "amount" in key.lower() or "total" in key.lower() or "salary" in key.lower() or key.endswith("_cents"):
            output_values[key] = rng.randint(10000, 500000)
        elif "score" in key.lower() or "rating" in key.lower():
            output_values[key] = rng.randint(1, 100)
        elif "date" in key.lower() or "time" in key.lower():
            month = rng.randint(1, 12)
            day = rng.randint(1, 28)
            output_values[key] = f"2024-{month:02d}-{day:02d}"
        elif "name" in key.lower() or "bucket_name" in key.lower() or "dashboard_name" in key.lower() or "campaign_name" in key.lower():
            output_values[key] = f"{rng.choice(['prod', 'staging', 'dev', 'test', 'demo'])}_{rng.choice(['app', 'service', 'data', 'web', 'api'])}_{rng.randint(100, 999)}"
        elif "previous" in key.lower() or "current" in key.lower() or "old" in key.lower() or "new" in key.lower():
            output_values[key] = rng.choice(["running", "stopped", "active", "inactive", "pending"])
        elif key == "namespace" or key == "cluster_ip":
            output_values[key] = f"10.{rng.randint(96, 99)}.0.{rng.randint(1, 254)}"
        elif key == "etag":
            output_values[key] = f'"{rng.randint(10000000000000000, 99999999999999999)}"'
        elif key == "version_id" or key == "version":
            output_values[key] = f"v{rng.randint(1, 50)}"
        elif key == "record_count":
            output_values[key] = rng.randint(100, 10000)
        elif key == "service_uid":
            output_values[key] = f"{rng.randint(10000000, 99999999)}-{rng.randint(1000, 9999)}"
        elif key == "webhook_url":
            output_values[key] = f"https://hooks.example.com/{rng.randint(100000, 999999)}"
        else:
            output_values[key] = f"{key}-{rng.randint(100, 999)}"

    return output_values


def _find_api_function(namespace, function_name):
    """Find an API function definition by namespace and function name."""
    key = (namespace, function_name)
    return API_LOOKUP.get(key)


def _validate_variable_refs(actions):
    """Validate all variable references in actions are valid.
    
    Checks:
    - Each {{steps[N].output.<key>}} references a step N that exists (0-indexed)
    - Step N's output_refs contains the referenced key
    - N < current action index (no forward references)
    
    Returns: (is_valid, errors) where errors is list of error strings
    """
    errors = []
    var_pattern = re.compile(r'\{\{steps\[(\d+)\]\.output\.(\w+)\}\}')
    
    for i, action in enumerate(actions):
        step_num = i + 1  # 1-indexed
        params = action.get("params", {})
        for pname, pvalue in params.items():
            if isinstance(pvalue, str):
                for match in var_pattern.finditer(pvalue):
                    ref_step = int(match.group(1))  # 1-indexed
                    output_key = match.group(2)
                    
                    # Check forward reference
                    if ref_step >= step_num:
                        errors.append(f"Step {step_num}: forward reference to step {ref_step} in param '{pname}'")
                        continue
                    
                    # Check step exists (0-indexed)
                    ref_idx = ref_step - 1
                    if ref_idx >= len(actions):
                        errors.append(f"Step {step_num}: references step {ref_step} which doesn't exist (only {len(actions)} steps)")
                        continue
                    
                    # Check output_refs has the key
                    ref_action = actions[ref_idx]
                    ref_outputs = ref_action.get("output_refs", {})
                    if output_key not in ref_outputs:
                        errors.append(f"Step {step_num}: references step {ref_step}.output.{output_key} but step {ref_step} has outputs {list(ref_outputs.keys())}")
                        continue
    
    return len(errors) == 0, errors


def _extract_variable_refs(params_dict):
    """Extract all {{steps[N].output.<key>}} references from a params dict.
    
    Returns: list of (step_num_1_indexed, key) tuples
    """
    refs = []
    var_pattern = re.compile(r'\{\{steps\[(\d+)\]\.output\.(\w+)\}\}')
    
    for pname, pvalue in params_dict.items():
        if isinstance(pvalue, str):
            for match in var_pattern.finditer(pvalue):
                refs.append((int(match.group(1)), match.group(2)))
    
    return refs


def _compute_complexity(actions, dependencies, rollback_steps_count):
    """Compute a complexity score for the sequence.
    
    Factors: step count, dependency edges, rollback branches, variable passing
    """
    n_steps = len(actions)
    n_deps = len(dependencies)
    
    # Count variable passing instances
    var_count = 0
    var_pattern = re.compile(r'\{\{steps\[\d+\]\.output\.\w+\}\}')
    for action in actions:
        for pname, pvalue in action.get("params", {}).items():
            if isinstance(pvalue, str):
                var_count += len(var_pattern.findall(pvalue))
    
    base_score = n_steps * 10
    dep_score = n_deps * 5
    rollback_score = rollback_steps_count * 15
    var_score = var_count * 8
    
    total = base_score + dep_score + rollback_score + var_score
    
    if n_steps <= 3:
        level = "simple"
    elif n_steps <= 6:
        level = "medium"
    else:
        level = "complex"
    
    return {
        "score": total,
        "level": level,
        "factors": {
            "step_count": n_steps,
            "dependency_count": n_deps,
            "rollback_count": rollback_steps_count,
            "variable_passing_count": var_count
        }
    }


def build_sequence(template, rng):
    """
    Convert an action template descriptor into a finalized JSON action sequence.
    
    Args:
        template: A template dict from TEMPLATES with keys: sector, domain, nl_template, actions
        rng: random.Random instance for reproducibility
    
    Returns:
        Dict with keys: input (will be filled by NL generator), actions, dependencies,
        variable_chain, complexity, sector, domain
        Or None if the template has unresolvable issues
    """
    sector = template.get("sector", "Unknown")
    domain = template.get("domain", "Unknown")
    nl_template = template.get("nl_template", "")
    
    # Collect all {placeholders} from the nl_template
    nl_placeholders = re.findall(r'\{(\w+)\}', nl_template)
    
    # Collect all {placeholders} from action params
    all_placeholders = set(nl_placeholders)
    for action in template.get("actions", []):
        for pname, pvalue in action.get("params", {}).items():
            if isinstance(pvalue, str):
                for ph in re.findall(r'\{(\w+)\}', pvalue):
                    if not ph.startswith("{") and not ph.endswith("}"):
                        all_placeholders.add(ph)
    
    # Generate values for all placeholders
    # Try to use realistic values from API function definitions
    params_dict = {}
    for ph in all_placeholders:
        # Check each action's API function for this parameter
        found_value = None
        for action in template.get("actions", []):
            api_fn = _find_api_function(action["namespace"], action["function"])
            if api_fn:
                pv = _get_param_values(api_fn)
                if ph in pv and pv[ph]["values"]:
                    found_value = rng.choice(pv[ph]["values"])
                    break
        if found_value is not None:
            params_dict[ph] = found_value
        else:
            # Generate synthetic values
            if "bool" in ph.lower():
                params_dict[ph] = rng.choice([True, False])
            elif any(x in ph.lower() for x in ["size", "port", "count", "replicas", "timeout"]):
                params_dict[ph] = rng.randint(1, 100)
            elif any(x in ph.lower() for x in ["amount", "price", "budget", "balance"]):
                params_dict[ph] = rng.randint(1000, 100000)
            elif any(x in ph.lower() for x in ["year", "month", "day", "date"]):
                params_dict[ph] = f"2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}"
            elif "email" in ph.lower():
                params_dict[ph] = f"{ph}@example.com"
            elif "env" in ph.lower() or "environment" in ph.lower():
                params_dict[ph] = rng.choice(["production", "staging", "development", "testing"])
            elif "region" in ph.lower():
                params_dict[ph] = rng.choice(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"])
            elif "priority" in ph.lower():
                params_dict[ph] = rng.choice(["high", "medium", "low", "critical"])
            elif "url" in ph.lower() or "link" in ph.lower():
                params_dict[ph] = f"https://example.com/{ph}-{rng.randint(100,999)}"
            elif "name" in ph.lower() or "title" in ph.lower() or "subject" in ph.lower():
                params_dict[ph] = f"{ph.replace('_', '-')}-{rng.randint(100,999)}"
            elif "type" in ph.lower():
                params_dict[ph] = rng.choice(["standard", "premium", "enterprise", "basic"])
            elif "desc" in ph.lower() or "description" in ph.lower():
                params_dict[ph] = f"Automated {ph.replace('_', ' ')} from template"
            else:
                params_dict[ph] = f"{ph.replace('_', '-')}-{rng.randint(10000, 99999)}"
    
    # Build actions
    resolved_actions = []
    prior_outputs = {}  # step_idx (1-indexed) -> {key: value}
    
    template_actions = template.get("actions", [])
    
    for idx, action_desc in enumerate(template_actions):
        step_number = idx + 1
        namespace = action_desc["namespace"]
        function_name = action_desc["function"]
        action_params = action_desc.get("params", {})
        depends_on = action_desc.get("depends_on", [])
        output_refs = action_desc.get("output_refs", {})
        rollback_ref_info = action_desc.get("rollback_ref", None)
        condition = action_desc.get("condition", None)
        
        # Look up the API function definition
        api_fn = _find_api_function(namespace, function_name)
        param_values = _get_param_values(api_fn) if api_fn else {}
        
        # Resolve parameters
        resolved_params = _resolve_params(action_params, params_dict, rng, prior_outputs, param_values)
        
        # Generate output values for output_refs
        output_values = _generate_output_values(output_refs, api_fn, resolved_params, rng)
        
        # Store in prior_outputs for variable chain
        if output_refs:
            prior_outputs[step_number] = {k: output_values.get(k, f"val-{k}") for k in output_refs}
        
        action_entry = {
            "step": step_number,
            "namespace": namespace,
            "function": function_name,
            "params": resolved_params,
            "depends_on": depends_on,
        }
        
        if output_refs:
            action_entry["output_refs"] = output_values
        
        if condition:
            action_entry["condition"] = condition
        
        if rollback_ref_info:
            action_entry["rollback_ref"] = rollback_ref_info
        
        resolved_actions.append(action_entry)
    
    # Now validate variable references
    is_valid, errors = _validate_variable_refs(template_actions)
    if not is_valid:
            return None, errors
    
    # Build dependency edges
    dependencies = []
    for action in resolved_actions:
        for dep in action.get("depends_on", []):
            dependencies.append({
                "from": dep,
                "to": action["step"]
            })
    
    # Build variable chain — use template_actions (unresolved) NOT resolved_actions
    # because _resolve_params() converts {{steps[N].output.<key>}} into concrete values,
    # making the patterns undetectable in resolved_actions.
# Build variable chain - scan TEMPLATE actions (before params are resolved)
    # because {{steps[N].output.<key>}} patterns are resolved by _resolve_params
    variable_chain = []
    for idx, action_desc in enumerate(template_actions):
        step_num = idx + 1
        params = action_desc.get("params", {})
        for pname, pvalue in params.items():
            if isinstance(pvalue, str):
                refs = re.findall(r'\{\{steps\[(\d+)\]\.output\.(\w+)\}\}', pvalue)
                for ref_step, ref_key in refs:
                    ref_step_int = int(ref_step)
                    if ref_step_int in prior_outputs and ref_key in prior_outputs[ref_step_int]:
                        variable_chain.append({
                            "from_step": ref_step_int,
                            "from_key": ref_key,
                            "from_value": prior_outputs[ref_step_int][ref_key],
                            "to_step": step_num,
                            "to_param": pname,
                            "to_value": prior_outputs[ref_step_int][ref_key]
                        })
    # Generate rollback action steps
    rollback_steps = []
    for idx, action in enumerate(resolved_actions):
        rollback_ref_info = action.get("rollback_ref")
        if rollback_ref_info:
            rb_step_number = len(resolved_actions) + len(rollback_steps) + 1
            rollback_action = {
                "step": rb_step_number,
                "namespace": rollback_ref_info.get("namespace", action["namespace"]),
                "function": rollback_ref_info.get("function", "Rollback"),
                "params": {
                    # Carry over key identifiers from the original action
                    k: v for k, v in action.get("params", {}).items()
                    if k.endswith("_id") or k.endswith("_name") or k in ["instance_id", "bucket_name", "function_name", "pipeline_name", "service_name", "deployment_name"]
                },
                "condition": "on_failure",
                "triggers_from": [action["step"]],
                "depends_on": [action["step"]],
            }
            
            # Add dependency edge for rollback
            dependencies.append({
                "from": action["step"],
                "to": rb_step_number,
                "type": "rollback_trigger"
            })
            
            rollback_steps.append(rollback_action)
    
    # Final variable reference validation on template actions (unresolved patterns)
    # NOTE: validating resolved_actions would always pass because _resolve_params()
    # already converted {{steps[N].output.<key>}} to concrete values.
        is_valid, errors = _validate_variable_refs(template_actions + rollback_steps)
        if not is_valid:
            return None, errors
    
    # Compute complexity
    complexity = _compute_complexity(resolved_actions, dependencies, len(rollback_steps))
    
    # Build final output
    result = {
        "actions": resolved_actions + rollback_steps,
        "dependencies": dependencies,
        "variable_chain": variable_chain,
        "complexity": complexity,
        "sector": sector,
        "domain": domain,
    }
    
    return result, None


def build_sequence_safe(template, rng, max_retries=5):
    """
    Safe wrapper for build_sequence that retries with different parameter sets on failure.
    
    Args:
        template: Template dict
        rng: random.Random instance
        max_retries: Maximum number of retry attempts
    
    Returns: (result, errors) where result is the sequence dict or None
    """
    for attempt in range(max_retries):
        result, errors = build_sequence(template, rng)
        if result is not None:
            return result, None
        # Advance rng to get different parameter values
        rng.random()
    
    return None, errors