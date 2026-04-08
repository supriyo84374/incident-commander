from models import Observation, Action

class Task3Env:
    """
    HARD: Three services running. worker_b has a memory leak.
    It causes CPU spike and network degradation on all services.
    Agent must: CHECK each service, KILL only worker_b, verify
    recovery, then submit POSTMORTEM with correct root cause.
    Killing wrong service = heavy penalty. No postmortem = score cap at 0.7.
    """
    MAX_STEPS = 20

    def reset(self):
        self.step_count = 0
        self.checks_done = set()
        self.killed_service = None
        self.correct_kill = False
        self.wrong_kills = 0
        self.postmortem_submitted = False
        self.postmortem_correct = False
        self.recovery_verified = False
        self.state = {
            "worker_a": {"status": "up", "cpu": 12.0, "memory": 14.0, "pid": 1021},
            "worker_b": {"status": "up", "cpu": 78.0, "memory": 91.0, "pid": 1055},
            "worker_c": {"status": "degraded", "cpu": 41.0, "memory": 38.0, "pid": 1089},
            "nginx": "degraded",
            "disk": 44.0,
            "logs": [
                "WARN  11:02:01 worker_c: response timeout 8s (threshold: 2s)",
                "ERROR 11:02:04 nginx: upstream timeout from worker pool",
                "WARN  11:02:07 worker_a: elevated latency detected",
                "ERROR 11:02:09 system: memory pressure — OOM risk",
                "CRIT  11:02:11 alertmanager: memory_usage > 90% on PID 1055"
            ],
            "alerts": [
                "CRITICAL: Memory pressure system-wide",
                "WARN: nginx upstream timeouts increasing",
                "WARN: worker_c degraded — cascading suspected"
            ]
        }
        return self._obs()

    def _obs(self):
        services = {
            "nginx": self.state["nginx"],
            "worker_a": self.state["worker_a"]["status"],
            "worker_b": self.state["worker_b"]["status"],
            "worker_c": self.state["worker_c"]["status"]
        }
        return Observation(
            logs=self.state["logs"][-5:],
            cpu_usage=self.state["worker_b"]["cpu"],
            memory_usage=self.state["worker_b"]["memory"],
            disk_usage=self.state["disk"],
            services_status=services,
            active_alerts=self.state["alerts"],
            step_count=self.step_count
        )

    def step(self, action: Action):
        self.step_count += 1
        cmd = action.command.strip().upper()
        reward = -0.05
        done = False
        info = {}

        if cmd.startswith("CHECK WORKER_A"):
            self.checks_done.add("worker_a")
            reward += 0.1
            self.state["logs"].append("INFO worker_a: cpu=12% mem=14% — nominal.")

        elif cmd.startswith("CHECK WORKER_B"):
            self.checks_done.add("worker_b")
            reward += 0.15
            self.state["logs"].append("INFO worker_b: cpu=78% mem=91% pid=1055 — LEAK CONFIRMED. Memory growing 2MB/s.")

        elif cmd.startswith("CHECK WORKER_C"):
            self.checks_done.add("worker_c")
            reward += 0.1
            self.state["logs"].append("INFO worker_c: cpu=41% mem=38% — degraded due to upstream pressure from worker_b.")

        elif cmd.startswith("CHECK NGINX"):
            self.checks_done.add("nginx")
            reward += 0.05
            self.state["logs"].append("INFO nginx: upstream timeouts caused by worker pool memory pressure.")

        elif cmd.startswith("KILL WORKER_B") or cmd == "KILL 1055":
            if "worker_b" in self.checks_done:
                self.correct_kill = True
                self.killed_service = "worker_b"
                self.state["worker_b"]["status"] = "down"
                self.state["worker_b"]["cpu"] = 0.0
                self.state["worker_b"]["memory"] = 0.0
                self.state["worker_c"]["status"] = "up"
                self.state["worker_c"]["cpu"] = 12.0
                self.state["nginx"] = "up"
                self.state["alerts"] = ["INFO: worker_b terminated. System recovering."]
                self.state["logs"].append("INFO: worker_b (PID 1055) killed. Memory pressure released.")
                reward += 0.4
            else:
                self.correct_kill = True
                self.killed_service = "worker_b"
                self.state["worker_b"]["status"] = "down"
                self.state["nginx"] = "up"
                reward += 0.2
                self.state["logs"].append("INFO: worker_b killed without full diagnosis.")

        elif cmd.startswith("KILL"):
            self.wrong_kills += 1
            reward -= 0.4
            self.state["logs"].append(f"ERROR: Wrong process killed — {action.command}. Outage worsened.")

        elif cmd.startswith("CHECK") and self.correct_kill:
            self.recovery_verified = True
            reward += 0.1
            self.state["logs"].append("INFO: Post-kill verification — all services nominal.")

        elif cmd.startswith("POSTMORTEM"):
            if self.correct_kill:
                self.postmortem_submitted = True
                raw = action.command.upper()
                if "WORKER_B" in raw and ("MEMORY" in raw or "LEAK" in raw):
                    self.postmortem_correct = True
                    reward += 0.35
                    self.state["logs"].append("INFO: Postmortem accepted. Root cause: worker_b memory leak.")
                    done = True
                    info["message"] = "full resolution with postmortem"
                else:
                    reward += 0.1
                    self.state["logs"].append("WARN: Postmortem submitted but root cause unclear.")
                    done = True
                    info["message"] = "postmortem incomplete"
            else:
                reward -= 0.1
                self.state["logs"].append("WARN: Cannot submit postmortem before resolving incident.")

        if self.step_count >= self.MAX_STEPS and not done:
            done = True
            reward -= 0.5
            info["message"] = "max steps exceeded"

        return self._obs(), reward, done, info

    def state(self):
        return self.state.copy()

    def grade(self) -> float:
        if not self.correct_kill:
            return 0.0
        base = 0.35
        check_bonus = len(self.checks_done) * 0.08
        if self.recovery_verified:
            base += 0.1
        if self.postmortem_submitted:
            base += 0.1
        if self.postmortem_correct:
            base += 0.15
        step_bonus = max(0.0, 0.15 * (1 - self.step_count / self.MAX_STEPS))
        penalty = self.wrong_kills * 0.2
        return round(min(1.0, max(0.0, base + check_bonus + step_bonus - penalty)), 3)
