package cmd

import (
	"github.com/MakeNowJust/heredoc"
	"github.com/atlanhq/atlan-cli/pkg/atlan"
	"github.com/spf13/cobra"
)

var (
	AppCommandShort = "Manage Atlan applications"
	AppCommandLong  = heredoc.Doc(`
		The app command helps you manage Atlan applications, including initialization,
		setup, release, and lifecycle management.
	`)
)

func buildAppCommand(a *atlan.Atlan) *cobra.Command {
	cmd := &cobra.Command{
		Use:     AppCommand,
		Short:   AppCommandShort,
		Long:    AppCommandLong,
		GroupID: CORE_GROUP,
		Hidden:  true, // Hide from help output until ready for public release
	}

	cmd.AddGroup(&cobra.Group{
		ID:    CORE_GROUP,
		Title: CORE_GROUP_TITLE,
	})

	// Register subcommands
	cmd.AddCommand(buildAppInitCommand(a))
	cmd.AddCommand(buildAppTemplateCommand(a))
	cmd.AddCommand(buildAppSampleCommand(a))
	cmd.AddCommand(buildAppRunCommand(a))
	cmd.AddCommand(buildAppTestCommand(a))
	cmd.AddCommand(buildAppReleaseCommand(a))

	return cmd
}
