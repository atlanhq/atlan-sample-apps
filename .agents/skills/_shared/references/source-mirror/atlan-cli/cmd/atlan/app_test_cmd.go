package cmd

import (
	"github.com/MakeNowJust/heredoc"
	"github.com/atlanhq/atlan-cli/pkg/atlan"
	"github.com/atlanhq/atlan-cli/pkg/logger"
	"github.com/spf13/cobra"
)

var (
	AppTestCommandShort = "Run application tests"
	AppTestCommandLong  = heredoc.Doc(`
		The atlan app test command runs tests for your Atlan application.

		Test types:
		- unit: Runs unit tests directly via 'uv run pytest tests/unit'
		- e2e: Starts dependencies, runs the app, waits for healthy, runs
		       'uv run pytest tests/e2e', then cleans up
		- all: Runs unit tests first, then e2e tests (default)

		E2E tests use the same ports as 'atlan app run'. Port defaults can be
		overridden via environment variables. See documentation for details.
	`)
	AppTestCommandExample = heredoc.Doc(`
		$ atlan app test                        # Run all tests
		$ atlan app test -t unit --coverage     # Run only unit tests with coverage report
		$ atlan app test -p ./my-app -v         # Run tests in specified directory with verbose output
	`)

	AppTestCommandPathFlag     = "Path to app directory"
	AppTestCommandTypeFlag     = "Test type: all, unit, e2e"
	AppTestCommandCoverageFlag = "Generate coverage report"
	AppTestCommandFailFastFlag = "Stop on first failure"
	AppTestCommandVerboseFlag  = "Show detailed output"
)

const (
	AppTestSubCommand = "test"
)

func buildAppTestCommand(a *atlan.Atlan) *cobra.Command {
	opts := atlan.AppTestOptions{
		Type: atlan.TestTypeAll,
	}

	cmd := &cobra.Command{
		Use:     AppTestSubCommand,
		Short:   AppTestCommandShort,
		Long:    AppTestCommandLong,
		Example: AppTestCommandExample,
		Args:    cobra.NoArgs,
		GroupID: CORE_GROUP,
		PreRunE: func(cmd *cobra.Command, args []string) error {
			defer logger.Log.Info("[PreCheck] finished command prechecks")

			// Skip tracking for app test - used repeatedly during development
			a.SegmentTrackEventInfo.SkipTracking = true

			return nil
		},
		Run: func(cmd *cobra.Command, args []string) {
			if atlanErr := a.AppTest(opts); atlanErr != nil {
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
		AppTestCommandPathFlag,
	)

	f.StringVarP(
		&opts.Type,
		TypeFlag,
		TypeFlagShorthand,
		atlan.TestTypeAll,
		AppTestCommandTypeFlag,
	)

	f.BoolVar(
		&opts.Coverage,
		CoverageFlag,
		false,
		AppTestCommandCoverageFlag,
	)

	f.BoolVar(
		&opts.FailFast,
		FailFastFlag,
		false,
		AppTestCommandFailFastFlag,
	)

	f.BoolVarP(
		&opts.Verbose,
		VerboseFlag,
		VerboseFlagShorthand,
		false,
		AppTestCommandVerboseFlag,
	)

	return cmd
}
