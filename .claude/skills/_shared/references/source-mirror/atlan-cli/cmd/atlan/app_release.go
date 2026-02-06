package cmd

import (
	"time"

	"github.com/MakeNowJust/heredoc"
	"github.com/atlanhq/atlan-cli/pkg/atlan"
	"github.com/atlanhq/atlan-cli/pkg/logger"
	"github.com/atlanhq/atlan-cli/pkg/utils"
	"github.com/spf13/cobra"
)

var (
	AppReleaseCommandShort = "Package, stage, and validate a Docker image"
	AppReleaseCommandLong  = heredoc.Doc(`
		The atlan app release command orchestrates the full release workflow:
		package → stage → validate (with scan check).

		This command:
		  1. Checks if Docker is running and Dockerfile exists
		  2. Packages the Docker image
		  3. Stages to the registry
		  4. Waits for vulnerability scan and adds label if no critical CVEs

		You can also run individual phases using subcommands:
		  • atlan app release package <image>  - Package only
		  • atlan app release stage <image>    - Stage only
		  • atlan app release validate <image> - Check scan and add label

		Credentials can be provided via flags (-u/--password), loaded from saved
		credentials, or prompted interactively. They are automatically saved for
		future use.
	`)
	AppReleaseCommandExample = heredoc.Doc(`
		# Release with default settings (prompts for credentials if not saved)
		$ atlan app release harbor.atlan.com/myproject/myapp:v1.0.0

		# Release from a specific directory with credentials
		$ atlan app release harbor.atlan.com/proj/app:v1 -p ./services/api -u myuser --password mypass

		# Skip validate phase (useful for CI/CD without credentials)
		$ atlan app release harbor.atlan.com/proj/app:v1 --skip-validate

		# Dry run: validate setup without building or pushing
		$ atlan app release harbor.atlan.com/proj/app:v1 --dry-run

	`)

	AppReleasePathFlagDesc = "Path to Dockerfile directory"
)

const (
	AppReleaseSubCommand = "release"
)

func buildAppReleaseCommand(a *atlan.Atlan) *cobra.Command {
	opts := atlan.AppReleaseOptions{}

	cmd := &cobra.Command{
		Use:     AppReleaseSubCommand + " <image>",
		Short:   AppReleaseCommandShort,
		Long:    AppReleaseCommandLong,
		Example: AppReleaseCommandExample,
		Args:    cobra.ExactArgs(1),
		GroupID: CORE_GROUP,
		PreRunE: func(cmd *cobra.Command, args []string) error {
			defer logger.Log.Info("[PreCheck] finished command prechecks")

			a.SegmentTrackEventInfo.SubModule = APP
			opts.Image = args[0]

			return nil
		},
		Run: func(cmd *cobra.Command, args []string) {
			startTime := time.Now()
			atlanErr := a.AppRelease(opts)
			a.SegmentTrackEventInfo.Properties.ExecutionTime = int(time.Since(startTime))
			if atlanErr != nil {
				a.HandleCommandError(atlanErr)
				return
			}
		},
		PostRun: func(cmd *cobra.Command, args []string) {
			logger.Log.Infof("[PostRun] running command app release post run with args %v", args)
			flags := []string{}

			if opts.Path != "" && opts.Path != "." {
				flags = append(flags, PathFlag)
			}

			if opts.Label != "" && opts.Label != atlan.ReplicateLabel {
				flags = append(flags, LabelFlag)
			}

			if opts.Username != "" {
				flags = append(flags, UsernameFlag)
			}

			if opts.Password != "" {
				flags = append(flags, PasswordFlag)
			}

			if opts.SkipValidate {
				flags = append(flags, SkipValidateFlag)
			}

			if opts.DryRun {
				flags = append(flags, DryRunFlag)
			}

			a.SetSegmentTrackProperties(
				nil,
				nil,
				utils.StringP(APP),
				utils.StringP(AppReleaseSubCommand),
				args,
				flags,
			)
		},
	}

	// Add subcommands
	cmd.AddCommand(buildAppReleasePackageCommand(a))
	cmd.AddCommand(buildAppReleaseStageCommand(a))
	cmd.AddCommand(buildAppReleaseValidateCommand(a))

	f := cmd.Flags()

	f.StringVarP(
		&opts.Path,
		PathFlag,
		PathFlagShorthand,
		".",
		AppReleasePathFlagDesc,
	)

	f.StringVarP(
		&opts.Label,
		LabelFlag,
		LabelFlagShorthand,
		atlan.ReplicateLabel,
		AppReleaseValidateFlagDesc,
	)

	f.StringVarP(
		&opts.Username,
		UsernameFlag,
		UsernameFlagShorthand,
		"",
		AppReleaseUsernameFlagDesc,
	)

	f.StringVar(
		&opts.Password,
		PasswordFlag,
		"",
		AppReleasePasswordFlagDesc,
	)

	f.BoolVar(
		&opts.SkipValidate,
		SkipValidateFlag,
		false,
		"Skip vulnerability scan and validate phase",
	)

	f.BoolVar(
		&opts.DryRun,
		DryRunFlag,
		false,
		"Validate setup without building or pushing (fast validation)",
	)

	return cmd
}
