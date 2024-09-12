
import subprocess

class SeafoilGit():
    def __init__(self):
        pass

    def run_git_command(self, command):
        """Run a Git command and return its output."""
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        if result.returncode != 0:
            raise Exception(f"Git command failed: {result.stderr.strip()}")
        return result.stdout.strip()

    def get_current_tag(self, ):
        """Get the current tag of the HEAD commit."""
        try:
            return self.run_git_command("git describe --tags --abbrev=0")
        except Exception as e:
            print(f"Error getting current tag: {e}")
            return None

    def get_last_tag(self):
        """Get the last tag of the repository."""
        try:
            return self.run_git_command("git describe --tags --abbrev=0 $(git rev-list --tags --max-count=1)")
        except Exception as e:
            print(f"Error getting last tag: {e}")
            return None

    def get_next_tag(self, current_tag):
        """Get the next tag after the current tag."""
        try:
            tags = self.run_git_command("git tag --sort=creatordate").split('\n')
            if current_tag in tags:
                current_index = tags.index(current_tag)
                if current_index + 1 < len(tags):
                    return tags[current_index + 1]
        except Exception as e:
            print(f"Error getting next tag: {e}")
        return None

    def checkout_to_tag(self, tag):
        """Checkout to the given tag."""
        try:
            self.run_git_command(f"git checkout {tag}")
            print(f"Checked out to tag: {tag}")
        except Exception as e:
            print(f"Error checking out to tag: {e}")

    # Update to last tag
    def update_to_last_tag(self):
        last_tag = self.get_last_tag()
        if last_tag:
            self.checkout_to_tag(last_tag)
            return last_tag
        return None

