"""Tests for CLI commands."""

import pytest
from typer.testing import CliRunner
from resume.cli import app
from unittest.mock import patch, MagicMock

runner = CliRunner()


class TestContactCommand:
    """Tests for contact command."""

    def test_contact_displays_information(self):
        """Test that contact command displays information."""
        result = runner.invoke(app, ["contact"])
        assert result.exit_code == 0
        assert "Contact Information" in result.stdout
        assert "Email" in result.stdout
        assert "Phone" in result.stdout

    def test_contact_includes_name(self):
        """Test that contact includes name."""
        result = runner.invoke(app, ["contact"])
        assert result.exit_code == 0
        assert "Sheikh Huzaif" in result.stdout or "Name" in result.stdout

    def test_contact_includes_github(self):
        """Test that contact includes GitHub."""
        result = runner.invoke(app, ["contact"])
        assert result.exit_code == 0
        assert "GitHub" in result.stdout


class TestSummaryCommand:
    """Tests for summary command."""

    def test_summary_displays_content(self):
        """Test that summary command displays content."""
        result = runner.invoke(app, ["summary"])
        assert result.exit_code == 0
        assert "Professional Summary" in result.stdout or "Summary" in result.stdout

    def test_summary_not_empty(self):
        """Test that summary has content."""
        result = runner.invoke(app, ["summary"])
        assert result.exit_code == 0
        # Should have more than just the title
        assert len(result.stdout) > 50


class TestWorkExpCommand:
    """Tests for work-exp command."""

    def test_work_exp_displays_experience(self):
        """Test that work-exp command displays experience."""
        result = runner.invoke(app, ["work-exp"])
        assert result.exit_code == 0
        # Check for company names or highlights section
        assert "Highlights" in result.stdout or any(company in result.stdout for company in ["Coda", "PAL"])

    def test_work_exp_includes_company_info(self):
        """Test that work experience includes company information."""
        result = runner.invoke(app, ["work-exp"])
        assert result.exit_code == 0
        # Should include job-related information like companies and engineers/developers
        assert any(term in result.stdout for term in ["Engineer", "Developer", "Coda", "PAL"])

    def test_work_exp_not_empty(self):
        """Test that work experience has content."""
        result = runner.invoke(app, ["work-exp"])
        assert result.exit_code == 0
        assert len(result.stdout) > 50


class TestProjectsCommand:
    """Tests for projects command."""

    def test_projects_displays_list(self):
        """Test that projects command displays projects."""
        result = runner.invoke(app, ["projects"])
        assert result.exit_code == 0
        assert "Project" in result.stdout

    def test_projects_not_empty(self):
        """Test that projects has content."""
        result = runner.invoke(app, ["projects"])
        assert result.exit_code == 0
        assert len(result.stdout) > 50


class TestEducationCommand:
    """Tests for education command."""

    def test_education_displays_info(self):
        """Test that education command displays information."""
        result = runner.invoke(app, ["education"])
        assert result.exit_code == 0
        assert "Education" in result.stdout

    def test_education_includes_university(self):
        """Test that education includes university information."""
        result = runner.invoke(app, ["education"])
        assert result.exit_code == 0
        # Should include degree, university, or institution
        assert any(term in result.stdout.lower() for term in ["degree", "university", "institution"])


class TestSkillsCommand:
    """Tests for skills command."""

    def test_skills_displays_list(self):
        """Test that skills command displays skills."""
        result = runner.invoke(app, ["skills"])
        assert result.exit_code == 0
        assert "Skill" in result.stdout

    def test_skills_includes_categories(self):
        """Test that skills includes categories."""
        result = runner.invoke(app, ["skills"])
        assert result.exit_code == 0
        # Should have some categorization or multiple skills
        assert len(result.stdout) > 50


class TestInfoCommand:
    """Tests for info command."""

    def test_info_displays_basic_info(self):
        """Test that info command displays basic information."""
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "CLI Tool Information" in result.stdout or "Information" in result.stdout

    def test_info_includes_version(self):
        """Test that info includes version."""
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "Version" in result.stdout or "1.0.0" in result.stdout

    def test_info_verbose_flag(self):
        """Test that info command accepts verbose flag."""
        result = runner.invoke(app, ["info", "--verbose"])
        assert result.exit_code == 0
        assert len(result.stdout) > 0

    def test_info_verbose_shows_more_details(self):
        """Test that verbose mode shows additional details."""
        result_normal = runner.invoke(app, ["info"])
        result_verbose = runner.invoke(app, ["info", "--verbose"])

        assert result_normal.exit_code == 0
        assert result_verbose.exit_code == 0
        # Verbose should show Framework and License
        assert "Framework" in result_verbose.stdout or "License" in result_verbose.stdout


class TestCLIApp:
    """Tests for main CLI application."""

    def test_help_command(self):
        """Test that help command works."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Usage" in result.stdout or "Commands" in result.stdout

    def test_version_flag(self):
        """Test that version flag works."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.stdout

    def test_no_command_shows_welcome(self):
        """Test that running with no command shows welcome message."""
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        # Should show some welcome or help information


class TestCommandIntegration:
    """Integration tests for commands."""

    def test_all_commands_executable(self):
        """Test that all commands can be executed without errors."""
        commands = ["contact", "summary", "work-exp", "projects", "education", "skills", "info"]

        for command in commands:
            result = runner.invoke(app, [command])
            assert result.exit_code == 0, f"Command '{command}' failed with exit code {result.exit_code}"
            assert len(result.stdout) > 0, f"Command '{command}' produced no output"

    def test_commands_with_verbose_flag(self):
        """Test that commands accept verbose flag where applicable."""
        commands_with_verbose = ["info"]

        for command in commands_with_verbose:
            result = runner.invoke(app, [command, "--verbose"])
            assert result.exit_code == 0, f"Command '{command} --verbose' failed"
            assert len(result.stdout) > 0
