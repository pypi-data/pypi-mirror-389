import click
import pandas as pd
from gresecml.core.session_manager import SessionManager
from gresecml.core.pcap_manager import lazy_read_packets
from gresecml.core.sniffer_manager import sniff_packets
from gresecml.core.progress_manager import ProgressManager
from gresecml.core.tensorflow_prediction_manager import tensorflow_predict

@click.group()
def tf():
    """Make predictions using TensorFlow."""
    pass

@click.command()
@click.option('--input', '-i', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True), help='Path to the .pcap file to analyze. If not provided, live capture will be used.')
@click.option('--output', '-o', type=click.Path(dir_okay=False, writable=True, resolve_path=True), default=None, help='Path to save the output HTML file. Default is None.')
@click.option('--enable-full-output', '-efo', is_flag=True, help='Enable full output including all features in the HTML and console output.')
@click.option('--prop-normal-max', '-pnm', type=int, default=None, help='Set the maximum normal traffic probability threshold(%) for output. Default is None (no threshold).')
@click.option('--lazy-load', '-ll', is_flag=True, help='Enable lazy loading. Predicts sessions one by one to save memory.')
@click.option('--iface', '-if', type=str, default=None, help='Network interface for live capture. If not provided, the default interface will be used.')
@click.option('--timeout', '-t', type=int, default=60, help='Timeout in seconds for live capture. Default is 60 seconds.')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
def predict(input, output, enable_full_output, prop_normal_max, lazy_load, iface, timeout, verbose):
    """Make predictions for a live capture or a given pcap file using TensorFlow."""
    try:
        click.echo(click.style(f"\nAnalyzing network traffic using tensorflow model.\n", fg='yellow', bold=True))

        # Initialize session manager
        session_manager = SessionManager()

        # Get packets depending on pcap file or live capture
        if input is None:
            returned_sessions = session_manager.start_processing(sniff_packets(iface=iface, timeout=timeout))
        else:
            returned_sessions = session_manager.start_processing(lazy_read_packets(input))

        if lazy_load:        
            # Lazy read packets and transform to sessions while making predictions
            progress_manager = ProgressManager()
            progress_manager.start(description="Processing network packets into sessions and making predictions")

            final_dataframe = pd.DataFrame()

            for session in returned_sessions:
                # Create input dictionary for prediction excluding non-feature columns
                input_dict = {col: session.iloc[0][col] for col in session.columns if col not in ['src_ip', 'dst_ip', 'src_port']}
                # Make predictions using TensorFlow model
                preds = tensorflow_predict(input_data=input_dict)
                
                # Update session with predictions
                for key, value in preds.items():
                    session[key] = value
                
                # Save session if it meets the normal probability threshold
                if prop_normal_max is not None:
                    if session.iloc[0]['prediction_normal'] * 100 <= prop_normal_max:
                        final_dataframe = pd.concat([final_dataframe, session], ignore_index=True)
                else:
                    final_dataframe = pd.concat([final_dataframe, session], ignore_index=True)

            progress_manager.stop()

            if verbose:
                print_dataframe(final_dataframe, enable_full_output)
                click.echo()  # New line for better readability
                    
            # Output results
            dataframe_to_html(final_dataframe, output, enable_full_output)
            
        if not lazy_load:
            # For predicting all sessions together after processing (stores all sessions in memory)
            # Load packets and transform to sessions
            progress_manager = ProgressManager()
            progress_manager.start(description="Processing network packets into sessions")

            sessions = pd.DataFrame()

            for session in returned_sessions:
                sessions = pd.concat([sessions, session], ignore_index=True)

            progress_manager.stop()
        
            # Make predictions using TensorFlow model
            progress_manager = ProgressManager(True)
            progress_manager.start(description="Making predictions", total=len(sessions))

            columns = sessions.columns.tolist()

            for idx, session in sessions.iterrows():
                input_dict = {col: session[col] for col in columns if col not in ['src_ip', 'dst_ip', 'src_port']}

                preds = tensorflow_predict(input_data=input_dict)
                
                for key, value in preds.items():
                    sessions.loc[idx, key] = value
                
                progress_manager.advance()

            progress_manager.stop()

            # Display predictions
            if prop_normal_max is not None:
                # Filter sessions based on normal traffic probability threshold
                filtered_sessions: pd.DataFrame = sessions[sessions['prediction_normal'] * 100 <= prop_normal_max]
                # Verbose output to console
                if verbose:
                    print_dataframe(filtered_sessions, enable_full_output)
                    click.echo() # New line for better readability
                # Output results
                dataframe_to_html(filtered_sessions, output, enable_full_output)
            else:
                # Verbose output to console
                if verbose:
                    print_dataframe(sessions, enable_full_output)
                    click.echo() # New line for better readability
                # Output results
                dataframe_to_html(sessions, output, enable_full_output)

        click.echo(click.style("\nPrediction process completed.\n", fg='yellow', bold=True))
    except Exception as e:
        click.echo(click.style(f"\nAn error occurred during prediction: \"{str(e)}\"\n", fg='red', bold=True))

tf.add_command(predict)

#----------------------------------------------------
# Methods for output handling
#----------------------------------------------------

# Convert DataFrame to HTML file with or without full output
def dataframe_to_html(df: pd.DataFrame, path: str = None, enable_full_output: bool = False):
    """Convert DataFrame to HTML file."""
    
    df = df.sort_values(by=['prediction_normal'], ascending=True)

    # Drop unwanted columns if they exist
    unwanted_columns = ['time_mean', 'time_std', 'bytes_mean', 'bytes_std', 'inter_arrival_std', 'inter_arrival_min', 'inter_arrival_max']

    if not enable_full_output:
        for col in unwanted_columns:
            if col in df.columns:
                df = df.drop(columns=[col])

    if path is not None:
        try:
            df.to_html(path, index=False)
            click.echo(click.style(f"Saved output to: {path}", fg='yellow'))
        except Exception as e:
            click.echo(click.style(f"Error saving output to: {path}\n{str(e)}", fg='red'))
            return


# Print DataFrame to console with or without full output
def print_dataframe(df: pd.DataFrame, enable_full_output: bool = False):
    """Print DataFrame to console."""

    df = df.sort_values(by=['prediction_normal'], ascending=True)

    # Drop unwanted columns if they exist
    unwanted_columns = ['time_mean', 'time_std', 'bytes_mean', 'bytes_std', 'inter_arrival_std', 'inter_arrival_min', 'inter_arrival_max', 'flag_syn_count', 'flag_ack_count', 'flag_fin_count', 'flag_rst_count', 'flag_dns_count', 'successful_connection', 'num_of_dest_unreachable']

    if not enable_full_output:
        for col in unwanted_columns:
            if col in df.columns:
                df = df.drop(columns=[col])

    click.echo(df.to_string(index=False))