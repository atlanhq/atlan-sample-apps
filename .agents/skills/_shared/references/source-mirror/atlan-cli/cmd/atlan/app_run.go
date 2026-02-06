package cmd

import (
	"github.com/MakeNowJust/heredoc"
	"github.com/atlanhq/atlan-cli/pkg/atlan"
	"github.com/atlanhq/atlan-cli/pkg/logger"
	"github.com/spf13/cobra"
)

var (
	AppRunCommandShort = "Run the application locally"
	AppRunCommandLong  = heredoc.Doc(`
		The atlan app run command starts a local development environment:
		1. Starts Temporal and Dapr in the background
		2. Runs the application in the foreground
		3. Handles graceful shutdown on Ctrl+C

		Dependencies are started via 'uv run poe start-deps' and stopped via
		'uv run poe stop-deps' when the application exits.

		Port defaults can be overridden via environment variables.
		See documentation for details.
	`)
	AppRunCommandExample = heredoc.Doc(`
		$ atlan app run                          # Run app in current directory
		$ atlan app run --no-watch               # Run without hot reload
		$ atlan app run -p ./my-app              # Run app in specified directory
	`)

	AppRunCommandPathFlag    = "Path to app directory"
	AppRunCommandNoWatchFlag = "Disable hot reload (hot reload is enabled by default)"
)

const (
	AppRunSubCommand = "run"
)

func buildAppRunCommand(a *atlan.Atlan) *cobra.Command {
	opts := atlan.AppRunOptions{}

	cmd := &cobra.Command{
		Use:     AppRunSubCommand,
		Short:   AppRunCommandShort,
		Long:    AppRunCommandLong,
		Example: AppRunCommandExample,
		Args:    cobra.NoArgs,
		GroupID: CORE_GROUP,
		PreRunE: func(cmd *cobra.Command, args []string) error {
			defer logger.Log.Info("[PreCheck] finished command prechecks")

			// Skip tracking for app run - used repeatedly during development
			a.SegmentTrackEventInfo.SkipTracking = true

			return nil
		},
		Run: func(cmd *cobra.Command, args []string) {
			if atlanErr := a.AppRun(opts); atlanErr != nil {
				a.HandleCommandError(atlanErr)
			}
		},
	}

	f := cmd.Flags()

	f.StringVarP(
		&opts.Path,
		PathFlag,
		PathFlagShorthand,
		".",
		AppRunCommandPathFlag,
	)

	f.BoolVar(
		&opts.NoWatch,
		NoWatchFlag,
		false,
		AppRunCommandNoWatchFlag,
	)

	return cmd
}
