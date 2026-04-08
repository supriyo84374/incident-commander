from models import Observation, Action

class Task2Env:
    """
    MEDIUM: Disk at 98%. Three directories are candidates.
    Only /var/log is the real culprit. CLEAN wrong path = penalty.
    Agent must CHECK disk, identify path, CLEAN correct one.
    """
    MAX_STEPS = 15

    def reset(self):
        self.step_count = 0
        self.checked_disk = False
        self.checked_varlog = False
        self.cleaned_correct = False
        self.wrong_cleans = 0
        self.state = {
            "nginx": "degraded",
            "postgres": "up",
            "redis": "up",
            "cpu": 22.0,
            "memory": 55.0,
            "disk": 98.0,
            "disk_breakdown": {
                "/var/log": "71G",
                "/home/ubuntu": "12G",
                "/tmp": "2G"
            },
            "logs": [
                "ERROR 07:45:01 kernel: No space left on device",
                "ERROR 07:45:03 nginx: could not write to access log — disk full",
                "WARN  07:45:10 postgres: checkpoint logging disabled",
                "INFO  07:45:12 df -h output: /dev/sda1  100G   98G  2G  98% /",
                "WARN  07:45:15 system: write operations failing across services"
            ],
            "alerts": [
                "CRITICAL: Disk usage 98% — write operations failing",
                "WARN: nginx access logs stalled"
            ]
        }
        return self._obs()

    def _obs(self):
        return Observation(
            logs=self.state["logs"][-5:],
            cpu_usage=self.state["cpu"],
            memory_usage=self.state["memory"],
            disk_usage=self.state["disk"],
            services_status={
                "nginx": self.state["nginx"],
                "postgres": self.state["postgres"],
                "redis": self.state["redis"]
            },
            active_alerts=self.state["alerts"],
            step_count=self.step_count
        )

    def step(self, action: Action):
        self.step_count += 1
        cmd = action.command.strip().upper()
        reward = -0.05
        done = False
        info = {}

        if "CHECK DISK" in cmd or "CHECK /VAR/LOG" in cmd:
            self.checked_disk = True
            if "/VAR/LOG" in cmd:
                self.checked_varlog = True
                reward += 0.2
                self.state["logs"].append("INFO: /var/log consuming 71G — rotated logs not purged in 47 days.")
            else:
                reward += 0.1
                self.state["logs"].append("INFO: Disk breakdown shown. Largest dir: /var/log at 71G.")

        elif "CLEAN /VAR/LOG" in cmd:
            if self.checked_disk:
                self.cleaned_correct = True
                self.state["disk"] = 41.0
                self.state["nginx"] = "up"
                self.state["alerts"] = []
                self.state["logs"].append("INFO: /var/log purged. Disk now at 41%. nginx resumed logging.")
                reward += 0.75
                done = True
                info["message"] = "disk cleared correctly"
            else:
                self.cleaned_correct = True
                self.state["disk"] = 41.0
                self.state["nginx"] = "up"
                reward += 0.35
                done = True
                info["message"] = "cleaned without diagnosis"

        elif "CLEAN /HOME" in cmd or "CLEAN /TMP" in cmd:
            self.wrong_cleans += 1
            reward -= 0.25
            self.state["logs"].append(f"WARN: Cleaned wrong directory: {action.command}. Disk still at 98%.")

        elif "RESTART" in cmd:
            reward -= 0.15
            self.state["logs"].append("WARN: Restarting services won't fix a full disk.")

        if self.step_count >= self.MAX_STEPS and not done:
            done = True
            reward -= 0.5
            info["message"] = "max steps exceeded"

        return self._obs(), reward, done, info

    def state(self):
        return self.state.copy()

    def grade(self) -> float:
        if not self.cleaned_correct:
            return 0.0
        base = 0.45
        if self.checked_disk:
            base += 0.2
        if self.checked_varlog:
            base += 0.15
        step_bonus = max(0.0, 0.2 * (1 - self.step_count / self.MAX_STEPS))
        penalty = self.wrong_cleans * 0.15
        return round(min(1.0, max(0.0, base + step_bonus - penalty)), 3)
