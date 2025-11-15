"""
Git Integration Tool for Meton.

Provides git repository operations:
- Repository status and analysis
- Diff generation and review
- Commit analysis and history
- AI-powered code review
- Commit message generation
- Branch operations
- File blame and history
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    import git
    from git import Repo, InvalidGitRepositoryError, GitCommandError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    Repo = None
    InvalidGitRepositoryError = Exception
    GitCommandError = Exception


class GitTool:
    """Git integration for repository analysis and operations."""

    def __init__(self, repo_path: str = "."):
        """
        Initialize Git tool.

        Args:
            repo_path: Path to git repository
        """
        if not GIT_AVAILABLE:
            raise ImportError("GitPython not installed. Run: pip install GitPython")

        self.repo_path = Path(repo_path).resolve()
        self.repo = self._initialize_repo()
        self.max_diff_size = 5000  # Max lines in diff

    def _initialize_repo(self) -> Optional[Repo]:
        """
        Initialize GitPython Repo object.

        Returns:
            Repo object or None if not a git repository
        """
        try:
            return Repo(self.repo_path, search_parent_directories=True)
        except InvalidGitRepositoryError:
            return None
        except Exception as e:
            print(f"Warning: Failed to initialize git repository: {e}")
            return None

    def is_git_repo(self) -> bool:
        """Check if current directory is a git repository."""
        return self.repo is not None

    def get_repo_status(self) -> Dict:
        """
        Get repository status.

        Returns:
            Repository status dictionary
        """
        if not self.repo:
            return {"error": "Not a git repository"}

        try:
            # Get current branch
            try:
                current_branch = self.repo.active_branch.name
            except TypeError:
                current_branch = "detached HEAD"

            # Get untracked, modified, and staged files
            untracked = self.repo.untracked_files
            modified = [item.a_path for item in self.repo.index.diff(None)]
            staged = [item.a_path for item in self.repo.index.diff("HEAD")]

            # Get ahead/behind remote
            ahead, behind = 0, 0
            try:
                if self.repo.active_branch.tracking_branch():
                    ahead_behind = self.repo.iter_commits(
                        f'{self.repo.active_branch.tracking_branch()}...{current_branch}'
                    )
                    ahead = sum(1 for _ in ahead_behind)

                    behind_iter = self.repo.iter_commits(
                        f'{current_branch}...{self.repo.active_branch.tracking_branch()}'
                    )
                    behind = sum(1 for _ in behind_iter)
            except (AttributeError, GitCommandError):
                pass

            return {
                "branch": current_branch,
                "is_dirty": self.repo.is_dirty(),
                "untracked_files": untracked,
                "modified_files": modified,
                "staged_files": staged,
                "ahead": ahead,
                "behind": behind
            }

        except Exception as e:
            return {"error": f"Failed to get status: {str(e)}"}

    def analyze_commit(self, commit_sha: str = "HEAD") -> Dict:
        """
        Analyze specific commit.

        Args:
            commit_sha: Commit SHA or reference (default: HEAD)

        Returns:
            Commit analysis dictionary
        """
        if not self.repo:
            return {"error": "Not a git repository"}

        try:
            commit = self.repo.commit(commit_sha)

            # Get changed files
            changed_files = []
            insertions = 0
            deletions = 0

            if commit.parents:
                diffs = commit.parents[0].diff(commit)
                changed_files = [diff.a_path or diff.b_path for diff in diffs]

                # Count insertions/deletions
                for diff in diffs:
                    if diff.diff:
                        diff_text = diff.diff.decode('utf-8', errors='ignore')
                        insertions += diff_text.count('\n+')
                        deletions += diff_text.count('\n-')
            else:
                # Initial commit
                changed_files = list(commit.stats.files.keys())
                insertions = sum(
                    commit.stats.files[f]['insertions']
                    for f in commit.stats.files
                )
                deletions = sum(
                    commit.stats.files[f]['deletions']
                    for f in commit.stats.files
                )

            return {
                "sha": commit.hexsha,
                "author": f"{commit.author.name} <{commit.author.email}>",
                "date": datetime.fromtimestamp(commit.committed_date).isoformat(),
                "message": commit.message.strip(),
                "files_changed": len(changed_files),
                "insertions": insertions,
                "deletions": deletions,
                "changed_files": changed_files
            }

        except Exception as e:
            return {"error": f"Failed to analyze commit: {str(e)}"}

    def get_diff(self, file_path: Optional[str] = None, staged: bool = False) -> str:
        """
        Get diff for file or entire working tree.

        Args:
            file_path: Optional specific file
            staged: Show staged changes (default: unstaged)

        Returns:
            Unified diff format string
        """
        if not self.repo:
            return "Error: Not a git repository"

        try:
            if staged:
                # Staged changes (index vs HEAD)
                if file_path:
                    diff = self.repo.index.diff("HEAD", paths=[file_path])
                else:
                    diff = self.repo.index.diff("HEAD")
            else:
                # Unstaged changes (working tree vs index)
                if file_path:
                    diff = self.repo.index.diff(None, paths=[file_path])
                else:
                    diff = self.repo.index.diff(None)

            if not diff:
                return "No changes to show"

            # Generate unified diff
            diff_text = []
            for item in diff:
                try:
                    diff_str = item.diff.decode('utf-8', errors='ignore')
                    diff_text.append(diff_str)
                except Exception:
                    diff_text.append(f"(binary file: {item.a_path or item.b_path})")

            result = '\n'.join(diff_text)

            # Truncate if too large
            lines = result.split('\n')
            if len(lines) > self.max_diff_size:
                result = '\n'.join(lines[:self.max_diff_size])
                result += f"\n\n... (truncated {len(lines) - self.max_diff_size} lines)"

            return result if result else "No changes to show"

        except Exception as e:
            return f"Error: Failed to get diff: {str(e)}"

    def suggest_commit_message(self, staged_only: bool = True) -> str:
        """
        Generate commit message from changes.

        Args:
            staged_only: Only analyze staged changes

        Returns:
            Conventional commit format message
        """
        if not self.repo:
            return "Error: Not a git repository"

        try:
            # Get diff
            diff = self.get_diff(staged=staged_only)

            if diff.startswith("Error") or diff == "No changes to show":
                return "No changes to commit"

            # Get changed files
            status = self.get_repo_status()
            changed_files = status.get("staged_files" if staged_only else "modified_files", [])

            if not changed_files:
                return "No changes to commit"

            # Analyze changes to determine type and scope
            commit_type = self._determine_commit_type(changed_files, diff)
            scope = self._determine_scope(changed_files)
            subject = self._generate_subject(changed_files, diff)

            # Build commit message
            if scope:
                header = f"{commit_type}({scope}): {subject}"
            else:
                header = f"{commit_type}: {subject}"

            # Add body with file list
            body_lines = []
            if len(changed_files) <= 5:
                body_lines.append("\nChanges:")
                for file in changed_files:
                    body_lines.append(f"- {file}")
            else:
                body_lines.append(f"\nModified {len(changed_files)} files")

            body = '\n'.join(body_lines)

            return f"{header}{body}"

        except Exception as e:
            return f"Error: Failed to generate commit message: {str(e)}"

    def get_file_history(self, file_path: str, max_commits: int = 10) -> List[Dict]:
        """
        Get commit history for specific file.

        Args:
            file_path: Path to file
            max_commits: Maximum commits to return

        Returns:
            List of commit dictionaries
        """
        if not self.repo:
            return [{"error": "Not a git repository"}]

        try:
            commits = list(self.repo.iter_commits(paths=file_path, max_count=max_commits))

            history = []
            for commit in commits:
                history.append({
                    "sha": commit.hexsha[:8],
                    "author": commit.author.name,
                    "date": datetime.fromtimestamp(commit.committed_date).strftime("%Y-%m-%d"),
                    "message": commit.message.strip().split('\n')[0]  # First line only
                })

            return history

        except Exception as e:
            return [{"error": f"Failed to get file history: {str(e)}"}]

    def get_branch_info(self) -> Dict:
        """
        Get branch information.

        Returns:
            Branch information dictionary
        """
        if not self.repo:
            return {"error": "Not a git repository"}

        try:
            try:
                current = self.repo.active_branch.name
                tracking = self.repo.active_branch.tracking_branch()
                tracking_name = tracking.name if tracking else None
            except TypeError:
                current = "detached HEAD"
                tracking_name = None

            all_branches = [str(b) for b in self.repo.branches]
            remote_branches = [str(b) for b in self.repo.remote().refs] if self.repo.remotes else []

            return {
                "current": current,
                "all_branches": all_branches,
                "remote_branches": remote_branches,
                "tracking": tracking_name
            }

        except Exception as e:
            return {"error": f"Failed to get branch info: {str(e)}"}

    def suggest_branch_name(self, description: str) -> str:
        """
        Generate branch name from description.

        Args:
            description: Branch description

        Returns:
            Valid git branch name
        """
        # Determine type from keywords
        desc_lower = description.lower()

        if any(word in desc_lower for word in ['bug', 'fix', 'issue', 'error']):
            prefix = "bugfix"
        elif any(word in desc_lower for word in ['hotfix', 'urgent', 'critical']):
            prefix = "hotfix"
        else:
            prefix = "feature"

        # Sanitize description
        # Remove special characters, replace spaces with hyphens
        name = re.sub(r'[^a-zA-Z0-9\s-]', '', description)
        name = re.sub(r'\s+', '-', name.strip())
        name = name.lower()

        # Limit length
        if len(name) > 50:
            name = name[:50]

        return f"{prefix}/{name}"

    def find_related_commits(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search commit history by message/author.

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            List of matching commits
        """
        if not self.repo:
            return [{"error": "Not a git repository"}]

        try:
            all_commits = list(self.repo.iter_commits(max_count=100))
            query_lower = query.lower()

            matching = []
            for commit in all_commits:
                if (query_lower in commit.message.lower() or
                    query_lower in commit.author.name.lower()):

                    matching.append({
                        "sha": commit.hexsha[:8],
                        "author": commit.author.name,
                        "date": datetime.fromtimestamp(commit.committed_date).strftime("%Y-%m-%d"),
                        "message": commit.message.strip().split('\n')[0]
                    })

                    if len(matching) >= max_results:
                        break

            return matching

        except Exception as e:
            return [{"error": f"Failed to search commits: {str(e)}"}]

    def get_blame(
        self,
        file_path: str,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None
    ) -> List[Dict]:
        """
        Git blame for file.

        Args:
            file_path: Path to file
            line_start: Optional start line
            line_end: Optional end line

        Returns:
            List of blame information per line
        """
        if not self.repo:
            return [{"error": "Not a git repository"}]

        try:
            # Get blame info
            blame_list = self.repo.blame("HEAD", file_path)

            result = []
            current_line = 1

            for commit, lines in blame_list:
                for line in lines:
                    # Check line range filter
                    if line_start and current_line < line_start:
                        current_line += 1
                        continue
                    if line_end and current_line > line_end:
                        break

                    result.append({
                        "line": current_line,
                        "author": commit.author.name,
                        "commit": commit.hexsha[:8],
                        "date": datetime.fromtimestamp(commit.committed_date).strftime("%Y-%m-%d"),
                        "content": line.strip()
                    })

                    current_line += 1

            return result

        except Exception as e:
            return [{"error": f"Failed to get blame: {str(e)}"}]

    def review_changes(self, file_path: Optional[str] = None) -> Dict:
        """
        Review uncommitted changes.

        Args:
            file_path: Optional specific file

        Returns:
            Review dictionary with suggestions
        """
        if not self.repo:
            return {"error": "Not a git repository"}

        try:
            diff = self.get_diff(file_path, staged=True)

            if diff.startswith("Error") or diff == "No changes to show":
                return {
                    "files": [],
                    "diff": diff,
                    "suggestions": ["No changes to review"],
                    "issues": []
                }

            # Extract changed files
            status = self.get_repo_status()
            files = status.get("staged_files", [])

            # Generate review suggestions (placeholder for AI integration)
            suggestions = self._generate_review_suggestions(diff, files)

            return {
                "files": files,
                "diff": diff,
                "suggestions": suggestions,
                "issues": []  # Placeholder for detailed issues
            }

        except Exception as e:
            return {"error": f"Failed to review changes: {str(e)}"}

    def _determine_commit_type(self, files: List[str], diff: str) -> str:
        """Determine conventional commit type from changes."""
        # Check file patterns
        test_files = any('test' in f.lower() for f in files)
        doc_files = any(f.endswith(('.md', '.rst', '.txt')) for f in files)

        # Check diff content
        diff_lower = diff.lower()

        if 'fix' in diff_lower or 'bug' in diff_lower:
            return 'fix'
        elif test_files:
            return 'test'
        elif doc_files:
            return 'docs'
        elif 'refactor' in diff_lower:
            return 'refactor'
        else:
            return 'feat'

    def _determine_scope(self, files: List[str]) -> Optional[str]:
        """Determine commit scope from changed files."""
        if not files:
            return None

        # Extract common directory or module
        if len(files) == 1:
            parts = Path(files[0]).parts
            if len(parts) > 1:
                return parts[0]

        # Find common path prefix
        common_parts = Path(files[0]).parts
        for file in files[1:]:
            parts = Path(file).parts
            common_parts = tuple(a for a, b in zip(common_parts, parts) if a == b)
            if not common_parts:
                break

        return common_parts[0] if common_parts else None

    def _generate_subject(self, files: List[str], diff: str) -> str:
        """Generate commit subject line."""
        if len(files) == 1:
            file_name = Path(files[0]).name
            return f"update {file_name}"
        else:
            # Generic subject based on file count
            return f"update {len(files)} files"

    def _generate_review_suggestions(self, diff: str, files: List[str]) -> List[str]:
        """Generate code review suggestions."""
        suggestions = []

        # Basic heuristics (placeholder for AI integration)
        if len(diff) > 10000:
            suggestions.append("Consider breaking this into smaller commits")

        if len(files) > 10:
            suggestions.append("Large number of files changed - ensure changes are related")

        if not suggestions:
            suggestions.append("Changes look reasonable - ready to commit")

        return suggestions

    def execute(self, action: str, **kwargs) -> str:
        """
        Execute git operations for agent.

        Args:
            action: Operation to perform
            **kwargs: Action-specific arguments

        Returns:
            Result string
        """
        if not self.is_git_repo():
            return "Error: Not a git repository"

        actions = {
            "status": lambda: self._format_status(self.get_repo_status()),
            "diff": lambda: self.get_diff(
                file_path=kwargs.get("file_path"),
                staged=kwargs.get("staged", False)
            ),
            "review": lambda: self._format_review(self.review_changes(
                file_path=kwargs.get("file_path")
            )),
            "commit_message": lambda: self.suggest_commit_message(
                staged_only=kwargs.get("staged_only", True)
            ),
            "history": lambda: self._format_history(self.get_file_history(
                file_path=kwargs.get("file_path", "."),
                max_commits=kwargs.get("max_commits", 10)
            )),
            "branch_info": lambda: self._format_branch_info(self.get_branch_info()),
            "suggest_branch": lambda: self.suggest_branch_name(kwargs.get("description", "")),
            "analyze_commit": lambda: self._format_commit(self.analyze_commit(
                commit_sha=kwargs.get("commit_sha", "HEAD")
            )),
            "blame": lambda: self._format_blame(self.get_blame(
                file_path=kwargs.get("file_path"),
                line_start=kwargs.get("line_start"),
                line_end=kwargs.get("line_end")
            ))
        }

        handler = actions.get(action)
        if not handler:
            return f"Error: Unknown action '{action}'"

        try:
            return handler()
        except Exception as e:
            return f"Error: {str(e)}"

    def _format_status(self, status: Dict) -> str:
        """Format status dictionary for display."""
        if "error" in status:
            return status["error"]

        lines = [
            f"Branch: {status['branch']}",
            f"Status: {'dirty' if status['is_dirty'] else 'clean'}",
        ]

        if status['ahead'] or status['behind']:
            lines.append(f"Sync: {status['ahead']} ahead, {status['behind']} behind")

        if status['untracked_files']:
            lines.append(f"\nUntracked files: {len(status['untracked_files'])}")
        if status['modified_files']:
            lines.append(f"Modified files: {len(status['modified_files'])}")
        if status['staged_files']:
            lines.append(f"Staged files: {len(status['staged_files'])}")

        return '\n'.join(lines)

    def _format_review(self, review: Dict) -> str:
        """Format review dictionary for display."""
        if "error" in review:
            return review["error"]

        lines = [f"Files reviewed: {len(review['files'])}"]

        if review['suggestions']:
            lines.append("\nSuggestions:")
            for suggestion in review['suggestions']:
                lines.append(f"- {suggestion}")

        return '\n'.join(lines)

    def _format_history(self, history: List[Dict]) -> str:
        """Format history list for display."""
        if not history:
            return "No commit history"

        if "error" in history[0]:
            return history[0]["error"]

        lines = ["Commit History:"]
        for commit in history:
            lines.append(f"  {commit['sha']} - {commit['date']} - {commit['author']}")
            lines.append(f"    {commit['message']}")

        return '\n'.join(lines)

    def _format_branch_info(self, info: Dict) -> str:
        """Format branch info for display."""
        if "error" in info:
            return info["error"]

        lines = [
            f"Current branch: {info['current']}",
            f"All branches: {', '.join(info['all_branches'])}"
        ]

        if info['tracking']:
            lines.append(f"Tracking: {info['tracking']}")

        return '\n'.join(lines)

    def _format_commit(self, commit: Dict) -> str:
        """Format commit analysis for display."""
        if "error" in commit:
            return commit["error"]

        return f"""Commit: {commit['sha']}
Author: {commit['author']}
Date: {commit['date']}
Message: {commit['message']}

Changes: {commit['files_changed']} files, +{commit['insertions']}/-{commit['deletions']}"""

    def _format_blame(self, blame: List[Dict]) -> str:
        """Format blame list for display."""
        if not blame:
            return "No blame information"

        if "error" in blame[0]:
            return blame[0]["error"]

        lines = ["Blame:"]
        for entry in blame[:20]:  # Limit display
            lines.append(f"  Line {entry['line']}: {entry['author']} ({entry['date']}) - {entry['commit']}")

        if len(blame) > 20:
            lines.append(f"  ... ({len(blame) - 20} more lines)")

        return '\n'.join(lines)
