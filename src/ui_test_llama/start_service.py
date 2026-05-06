import os
import subprocess
import json
import re
import time
import sys
import shlex

from pathlib import Path

WRAPPER_FILENAME = "start-wrapper.cjs"
DETECTION_TIMEOUT = 60  # seconds
PM2_LOG_DIR = os.path.expanduser("~/.pm2/logs")

WRAPPER_TEMPLATE = """
const {{ spawn }} = require('child_process');

const child = spawn({command}, {args}, {{
  shell: true,
  stdio: 'inherit',
  windowsHide: true
}});

child.on('error', err => {{
  console.error('Failed to start child process:', err);
}});
"""

def remove_files_in_dir(dir_path: str) -> None:
    """
    Delete every regular file in *dir_path*.
    Sub‑directories (and their contents) are left untouched.
    """
    for entry in os.listdir(dir_path):
        fp = os.path.join(dir_path, entry)
        if os.path.isfile(fp):
            os.remove(fp)


def load_json(in_file):
    with open(in_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def find_node_apps(base_dir):
    return [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]


def parse_start_command(command_str):
    parts = shlex.split(command_str)
    command = json.dumps(parts[0])
    args = json.dumps(parts[1:])
    return command, args


def create_wrapper_script(app_dir, start_command):
    command, args = parse_start_command(start_command)
    script_content = WRAPPER_TEMPLATE.format(command=command, args=args)
    # replace("{command}", command).replace("{args}", args)
    wrapper_path = os.path.join(app_dir, WRAPPER_FILENAME)
    with open(wrapper_path, "w", encoding="utf-8") as f:
        f.write(script_content.strip())
    print(f"📝 Created wrapper in {wrapper_path}")


def generate_ecosystem_config(apps, base_dir, commands):
    apps_config = []
    for app in apps:
        app_path = os.path.join(base_dir, app).replace("\\", "/")
        create_wrapper_script(app_path, commands[app]["last_start_action"])
        apps_config.append({
            "name": app,
            "cwd": app_path,
            "script": "node",
            "args": WRAPPER_FILENAME
        })
    return {"apps": apps_config}


def write_ecosystem_file(config, output_file):
    content = "module.exports = " + json.dumps(config, indent=2) + ";"
    with open(output_file, "w") as f:
        f.write(content)
    print(f"✅ Generated {output_file}")


# def run_npm_install(apps, base_dir, commands):
#     for app in apps:
#         print(f"📦 Installing dependencies for {app}...")
#         for cmd in commands[app]["shell_actions"]:
#             subprocess.run(cmd, shell=True, cwd=os.path.join(base_dir, app), check=True)


def remove_npm_run_dev(command_line: str) -> str:
    parts = [part.strip() for part in command_line.split("&&")]
    filtered_parts = [part for part in parts if part != "npm run dev" and part != "npm run start" and part != "npm start"]
    return " && ".join(filtered_parts)


def _add_flag(cmd: str, flag: str) -> str:
    """
    Insert an extra flag (e.g. --force) right after every occurrence of
    `npm install` in the command string, unless it is already present.
    """
    pattern = r"(npm\s+install)(?![^&]*\b" + re.escape(flag) + r"\b)"
    replacement = rf"\1 {flag}"
    return re.sub(pattern, replacement, cmd)


def run_npm_install(apps, base_dir, commands):
    """
    Run npm install commands for each app, retrying with --force and then
    --legacy-peer-deps if the original command fails.  Errors are logged but
    never propagate, so the calling code keeps running.
    """
    for app in apps:
        cwd = Path(base_dir) / app
        print(f"📦 Installing dependencies for {app}…")

        for raw_cmd in commands[app]["shell_actions"]:
            raw_cmd = remove_npm_run_dev(raw_cmd)
            # Build the three attempts
            attempts = [
                raw_cmd,
                _add_flag(raw_cmd, "--force"),
                _add_flag(raw_cmd, "--legacy-peer-deps"),
            ]

            for idx, cmd in enumerate(attempts, start=1):
                try:
                    print(f"  ▶ Attempt {idx}: {cmd}")
                    subprocess.run(cmd, shell=True, cwd=cwd, check=True)
                    print("  ✅ Success\n")
                    break                       # success → next shell_action
                except subprocess.CalledProcessError as e:
                    print(f"  ⚠️  Attempt {idx} failed (exit {e.returncode})")
            else:
                # all attempts failed
                print(f"  ❌ Giving up on {raw_cmd}\n")


def run_command(cmd):
    kwargs = dict(shell=True)
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    subprocess.run(cmd, **kwargs)


def start_pm2(ecosystem_file):
    print("🚀 Starting apps with PM2...")
    run_command("pm2 delete all")
    run_command(f"pm2 start {ecosystem_file}")


def detect_ports_from_pm2_logs(apps):
    results = {}
    print("🔍 Detecting ports from PM2 logs...")
    
    # Common port patterns in dev server output
    port_patterns = [
        re.compile(r"http[s]?://(?:localhost|127\.0\.0\.1):(\d+)", re.IGNORECASE),
        re.compile(r"[Ll]istening on (?:port )?(?:localhost:|127\.0\.0\.1:)?(\d+)"),
        re.compile(r"[Ss]erver running (?:at|on) (?:port )?(?:localhost:|127\.0\.0\.1:)?(\d+)"),
        re.compile(r"[Dd]ev [Ss]erver running at .*:(\d+)"),
        re.compile(r"[Pp]ort (\d+) is already in use"),  # Fallback pattern
    ]
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

    start_time = time.time()
    while time.time() - start_time < DETECTION_TIMEOUT:
        for app in apps:
            if app in results:
                continue

            log_file = os.path.join(PM2_LOG_DIR, f"{app}-out.log")
            error_log = os.path.join(PM2_LOG_DIR, f"{app}-error.log")
            
            # Try both output and error logs
            for current_log in [log_file, error_log]:
                if not os.path.exists(current_log):
                    continue

                try:
                    with open(current_log, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        content = ansi_escape.sub('', content).strip()
                        
                        # Try each pattern
                        for pattern in port_patterns:
                            match = pattern.search(content)
                            if match:
                                try:
                                    port = int(match.group(1))
                                    if 1024 <= port <= 65535:  # Validate port range
                                        print(f"✅ {app} is running on port {port}")
                                        results[app] = port
                                        break
                                except ValueError:
                                    continue
                except Exception as e:
                    print(f"Warning: Error reading log for {app}: {str(e)}")

        if len(results) == len(apps):
            break

        # Print status of undetected apps
        missing_apps = set(apps) - set(results.keys())
        if missing_apps:
            print(f"⏳ Still waiting for ports from: {', '.join(missing_apps)}")

        time.sleep(2)

    # Report any apps where we couldn't detect ports
    missing_apps = set(apps) - set(results.keys())
    if missing_apps:
        print(f"⚠️ Could not detect ports for: {', '.join(missing_apps)}")

    return results


def start_services(base_dir, commands):
    remove_files_in_dir(PM2_LOG_DIR)
    if not os.path.exists(base_dir):
        print(f"❌ Path does not exist: {base_dir}")
        return
    
    for app in commands.keys():
        if commands[app]["shell_actions"] is None or len(commands[app]["shell_actions"]) == 0:
            commands[app]["shell_actions"] = ["npm install"]
        if commands[app]["last_start_action"] is None or len(commands[app]["last_start_action"]) == 0:
            commands[app]["last_start_action"] = "npx vite --host"
            package_json = os.path.join(base_dir, app, "package.json")
            if os.path.isfile(package_json):
                data = load_json(package_json)
                if "scripts" in data.keys() and "dev" not in data["scripts"] and "start" in data["scripts"]:
                    commands[app]["last_start_action"] = "npm run start"

    ecosystem_path = os.path.join(base_dir, "ecosystem.config.js")
    output_path = os.path.join(base_dir, "services.json")

    apps = commands.keys()
    if not apps:
        print("❌ No Node.js apps found.")
        return

    run_npm_install(apps, base_dir, commands)

    config = generate_ecosystem_config(apps, base_dir, commands)
    write_ecosystem_file(config, ecosystem_path)

    start_pm2(ecosystem_path)

    ports = detect_ports_from_pm2_logs(apps)

    with open(output_path, "w") as f:
        json.dump(ports, f, indent=2)

    print(f"📄 Saved service ports to {output_path}")
    return ports
