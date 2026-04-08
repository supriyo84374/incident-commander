from models import Observation, Action

class Task1Env:
    """
    EASY: nginx is down. Agent must CHECK logs, then RESTART nginx.
    Penalized for restarting wrong services or too many steps.
    """
    MAX_STEPS = 10

    def reset(self):
        self.step_count = 0
        self.nginx_restarted = False
        self.checked_logs = False
        self.wrong_restarts = 0
        self.state = {
            "nginx": "down",
            "postgres": "up",
            "redis": "up",
            "cpu": 18.0,
            "memory": 42.0,
            "disk": 38.0,
            "logs": [
                "ERROR 03:12:01 nginx: worker process exited with code 1",
                "ERROR 03:12:03 nginx: bind() to 0.0.0.0:80 failed",
                "WARN  03:12:05 healthcheck: nginx not responding on port 80",
                "INFO  03:12:10 postgres: connection pool healthy",
                "INFO  03:12:10 redis: ping OK"
            ],
            "alerts": ["CRITICAL: nginx DOWN — site unreachable"]
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
                "postgres": "up",
                "redis": "up"
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

        if cmd.startswith("CHECK"):
            self.checked_logs = True
            reward += 0.15
            self.state["logs"].append("INFO: Log check performed. nginx failure confirmed on port 80.")

        elif cmd.startswith("RESTART NGINX"):
            if self.checked_logs:
                self.nginx_restarted = True
                self.state["nginx"] = "up"
                self.state["alerts"] = []
                self.state["logs"].append("INFO: nginx restarted successfully. Port 80 responding.")
                reward += 0.8
                done = True
                info["message"] = "nginx restored"
            else:
                self.nginx_restarted = True
                self.state["nginx"] = "up"
                self.state["alerts"] = []
                reward += 0.4
                done = True
                info["message"] = "nginx restored but no diagnosis performed"

        elif cmd.startswith("RESTART"):
            self.wrong_restarts += 1
            reward -= 0.3
            self.state["logs"].append(f"WARN: Unnecessary restart attempted: {action.command}")

        if self.step_count >= self.MAX_STEPS and not done:
            done = True
            reward -= 0.5
            info["message"] = "max steps exceeded"

        return self._obs(), reward, done, info

    def state(self):
        return self.state.copy()

    def grade(self) -> float:
        if not self.nginx_restarted:
            return 0.0
        base = 0.5
        if self.checked_logs:
            base += 0.3
        step_bonus = max(0.0, 0.2 * (1 - self.step_count / self.MAX_STEPS))
        penalty = self.wrong_restarts * 0.1
        return round(min(1.0, max(0.0, base + step_bonus - penalty)), 3)
