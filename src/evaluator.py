import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import required modules
from tts.tts_manager import TTSManager
from stt.stt_manager import STTManager
from llm.llm_manager import LLMManager
from audio.audio_manager import AudioManager
from turn_taking.turn_manager import TurnManager
from agents.agent_manager import AgentManager

class Evaluator:
    """
    Evaluates the performance of the multi-voice agent system.
    Provides metrics and benchmarks for various components.
    """
    
    def __init__(self, config_dir='./config'):
        """
        Initialize the evaluator with configuration.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.initialize_components()
        
    def initialize_components(self):
        """Initialize all system components for evaluation"""
        print("Initializing evaluation components...")
        
        # Initialize managers
        self.audio_manager = AudioManager(self.config_dir / 'audio_config.json')
        self.tts_manager = TTSManager(self.config_dir / 'tts_config.json')
        self.stt_manager = STTManager(self.config_dir / 'stt_config.json')
        self.llm_manager = LLMManager(self.config_dir / 'llm_config.json')
        self.turn_manager = TurnManager(self.config_dir / 'agent_config.json')
        self.agent_manager = AgentManager(
            self.config_dir / 'agent_config.json',
            self.llm_manager,
            self.tts_manager
        )
        
        print("All components initialized successfully")
    
    def evaluate_tts_performance(self, output_dir='./evaluation/tts'):
        """
        Evaluate TTS performance metrics.
        
        Args:
            output_dir: Directory to save evaluation results
            
        Returns:
            Dictionary with TTS performance metrics
        """
        print("Evaluating TTS performance...")
        os.makedirs(output_dir, exist_ok=True)
        
        metrics = {}
        test_texts = [
            "This is a short test sentence.",
            "This is a medium length test sentence with some more words to evaluate the performance.",
            "This is a longer test sentence that contains multiple clauses, some punctuation, and should test the TTS engine's ability to handle more complex linguistic structures and maintain proper intonation throughout the entire utterance."
        ]
        
        for agent_id in ["alex", "jordan", "taylor"]:
            agent_metrics = {}
            
            for i, text in enumerate(test_texts):
                start_time = os.times().elapsed
                
                # Generate speech
                output_path = os.path.join(output_dir, f"{agent_id}_test_{i}.wav")
                audio_path = self.tts_manager.generate_speech(text, agent_id, output_path)
                
                end_time = os.times().elapsed
                generation_time = end_time - start_time
                
                # Get file size
                file_size = os.path.getsize(audio_path) if audio_path else 0
                
                agent_metrics[f"test_{i}"] = {
                    "text": text,
                    "generation_time_seconds": generation_time,
                    "file_size_bytes": file_size,
                    "audio_path": audio_path
                }
            
            metrics[agent_id] = agent_metrics
        
        # Save metrics to file
        import json
        with open(os.path.join(output_dir, "tts_metrics.json"), "w") as f:
            json.dump(metrics, f, indent=2)
        
        print(f"TTS evaluation complete. Results saved to {output_dir}")
        return metrics
    
    def evaluate_stt_performance(self, test_audio_dir='./data/test_audio', output_dir='./evaluation/stt'):
        """
        Evaluate STT performance metrics.
        
        Args:
            test_audio_dir: Directory containing test audio files
            output_dir: Directory to save evaluation results
            
        Returns:
            Dictionary with STT performance metrics
        """
        print("Evaluating STT performance...")
        os.makedirs(output_dir, exist_ok=True)
        
        metrics = {}
        
        # Check if test audio directory exists
        if not os.path.exists(test_audio_dir):
            print(f"Test audio directory {test_audio_dir} not found")
            return metrics
        
        # Get all WAV files in test directory
        test_files = [f for f in os.listdir(test_audio_dir) if f.endswith('.wav')]
        
        for test_file in test_files:
            file_path = os.path.join(test_audio_dir, test_file)
            
            start_time = os.times().elapsed
            
            # Transcribe audio
            transcription = self.stt_manager.transcribe_file(file_path)
            
            end_time = os.times().elapsed
            transcription_time = end_time - start_time
            
            metrics[test_file] = {
                "transcription": transcription,
                "transcription_time_seconds": transcription_time,
                "file_size_bytes": os.path.getsize(file_path)
            }
        
        # Save metrics to file
        import json
        with open(os.path.join(output_dir, "stt_metrics.json"), "w") as f:
            json.dump(metrics, f, indent=2)
        
        print(f"STT evaluation complete. Results saved to {output_dir}")
        return metrics
    
    def evaluate_llm_performance(self, output_dir='./evaluation/llm'):
        """
        Evaluate LLM performance metrics.
        
        Args:
            output_dir: Directory to save evaluation results
            
        Returns:
            Dictionary with LLM performance metrics
        """
        print("Evaluating LLM performance...")
        os.makedirs(output_dir, exist_ok=True)
        
        metrics = {}
        test_prompts = [
            "What are your thoughts on artificial intelligence?",
            "How might digital transformation affect small businesses?",
            "What social implications do you see from increased automation?"
        ]
        
        for agent_id in ["alex", "jordan", "taylor"]:
            agent = self.agent_manager.get_agent_by_id(agent_id)
            agent_metrics = {}
            
            for i, prompt in enumerate(test_prompts):
                start_time = os.times().elapsed
                
                # Generate response
                system_prompt = self.agent_manager._build_system_prompt(agent)
                response = self.llm_manager.generate_response(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    agent_id=agent_id
                )
                
                end_time = os.times().elapsed
                generation_time = end_time - start_time
                
                agent_metrics[f"prompt_{i}"] = {
                    "prompt": prompt,
                    "response": response,
                    "generation_time_seconds": generation_time,
                    "response_length": len(response) if response else 0
                }
            
            metrics[agent_id] = agent_metrics
        
        # Save metrics to file
        import json
        with open(os.path.join(output_dir, "llm_metrics.json"), "w") as f:
            json.dump(metrics, f, indent=2)
        
        print(f"LLM evaluation complete. Results saved to {output_dir}")
        return metrics
    
    def evaluate_turn_taking(self, output_dir='./evaluation/turn_taking'):
        """
        Evaluate turn-taking performance metrics.
        
        Args:
            output_dir: Directory to save evaluation results
            
        Returns:
            Dictionary with turn-taking performance metrics
        """
        print("Evaluating turn-taking performance...")
        os.makedirs(output_dir, exist_ok=True)
        
        metrics = {}
        
        # Simulate a conversation
        conversation = [
            {"speaker": "audience", "text": "What do you all think about the future of remote work?", "is_audience": True},
            {"speaker": "alex", "text": "I believe remote work will continue to evolve with better virtual collaboration tools and AI assistants.", "is_audience": False},
            {"speaker": "jordan", "text": "From a business perspective, hybrid models will likely dominate as they balance flexibility with team cohesion.", "is_audience": False},
            {"speaker": "audience", "text": "Taylor, what about the social aspects?", "is_audience": True},
            {"speaker": "taylor", "text": "Great question! I'm concerned about potential isolation, but also excited about the possibilities for more inclusive workplaces and better work-life balance.", "is_audience": False},
            {"speaker": "alex", "text": "Building on that, I think we'll see more investment in virtual reality spaces for social connection.", "is_audience": False}
        ]
        
        # Reset turn manager
        self.turn_manager = TurnManager(self.config_dir / 'agent_config.json')
        
        # Simulate the conversation
        for i, message in enumerate(conversation):
            speaker = message["speaker"]
            text = message["text"]
            is_audience = message["is_audience"]
            
            # Start speaking
            if is_audience:
                self.turn_manager.start_speaking(speaker, is_audience=True)
            else:
                self.turn_manager.start_speaking(speaker)
            
            # Add to conversation history
            self.agent_manager.add_to_conversation(speaker, text, is_audience)
            
            # Stop speaking
            self.turn_manager.stop_speaking()
            
            # If not the last message, determine next speaker
            if i < len(conversation) - 1:
                next_message = conversation[i + 1]
                expected_next = next_message["speaker"]
                
                # Get next speaker from turn manager
                actual_next = self.turn_manager.get_next_speaker(text, audience_active=next_message["is_audience"])
                
                # Record result
                metrics[f"turn_{i}"] = {
                    "current_speaker": speaker,
                    "is_audience": is_audience,
                    "text": text,
                    "expected_next": expected_next,
                    "actual_next": actual_next,
                    "match": (expected_next == actual_next) or (next_message["is_audience"] and actual_next is None)
                }
        
        # Get overall turn statistics
        metrics["statistics"] = self.turn_manager.get_turn_statistics()
        
        # Save metrics to file
        import json
        with open(os.path.join(output_dir, "turn_taking_metrics.json"), "w") as f:
            json.dump(metrics, f, indent=2)
        
        print(f"Turn-taking evaluation complete. Results saved to {output_dir}")
        return metrics
    
    def evaluate_audio_routing(self, output_dir='./evaluation/audio'):
        """
        Evaluate audio routing performance.
        
        Args:
            output_dir: Directory to save evaluation results
            
        Returns:
            Dictionary with audio routing performance metrics
        """
        print("Evaluating audio routing performance...")
        os.makedirs(output_dir, exist_ok=True)
        
        metrics = {
            "available_devices": self.audio_manager.list_audio_devices(),
            "input_device": self.audio_manager.input_device_index,
            "output_device": self.audio_manager.output_device_index
        }
        
        # Test audio playback latency
        test_audio = os.path.join(output_dir, "test_playback.wav")
        
        # Generate a test audio file if it doesn't exist
        if not os.path.exists(test_audio):
            # Use TTS to generate a test audio file
            self.tts_manager.generate_speech(
                "This is a test of the audio routing system.", 
                "alex", 
                test_audio
            )
        
        if os.path.exists(test_audio):
            start_time = os.times().elapsed
            
            # Play audio
            self.audio_manager.play_audio(test_audio, blocking=True)
            
            end_time = os.times().elapsed
            playback_time = end_time - start_time
            
            metrics["playback_test"] = {
                "file": test_audio,
                "file_size_bytes": os.path.getsize(test_audio),
                "playback_time_seconds": playback_time
            }
        
        # Save metrics to file
        import json
        with open(os.path.join(output_dir, "audio_routing_metrics.json"), "w") as f:
            json.dump(metrics, f, indent=2)
        
        print(f"Audio routing evaluation complete. Results saved to {output_dir}")
        return metrics
    
    def run_all_evaluations(self):
        """Run all evaluation metrics and generate a summary report"""
        print("Running all evaluations...")
        
        # Create evaluation directory
        eval_dir = Path("./evaluation")
        eval_dir.mkdir(parents=True, exist_ok=True)
        
        # Run individual evaluations
        tts_metrics = self.evaluate_tts_performance()
        stt_metrics = self.evaluate_stt_performance()
        llm_metrics = self.evaluate_llm_performance()
        turn_metrics = self.evaluate_turn_taking()
        audio_metrics = self.evaluate_audio_routing()
        
        # Generate summary report
        summary = {
            "tts_summary": self._summarize_tts_metrics(tts_metrics),
            "stt_summary": self._summarize_stt_metrics(stt_metrics),
            "llm_summary": self._summarize_llm_metrics(llm_metrics),
            "turn_summary": self._summarize_turn_metrics(turn_metrics),
            "audio_summary": self._summarize_audio_metrics(audio_metrics)
        }
        
        # Save summary to file
        import json
        with open(eval_dir / "evaluation_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        # Generate HTML report
        self._generate_html_report(summary, eval_dir / "evaluation_report.html")
        
        print(f"All evaluations complete. Summary saved to {eval_dir / 'evaluation_summary.json'}")
        print(f"HTML report saved to {eval_dir / 'evaluation_report.html'}")
        
        return summary
    
    def _summarize_tts_metrics(self, metrics):
        """Summarize TTS metrics"""
        if not metrics:
            return {"status": "No data"}
        
        summary = {}
        for agent_id, agent_metrics in metrics.items():
            avg_time = sum(m["generation_time_seconds"] for m in agent_metrics.values()) / len(agent_metrics)
            summary[agent_id] = {
                "average_generation_time": avg_time,
                "tests_completed": len(agent_metrics)
            }
        
        return summary
    
    def _summarize_stt_metrics(self, metrics):
        """Summarize STT metrics"""
        if not metrics:
            return {"status": "No data"}
        
        avg_time = sum(m["transcription_time_seconds"] for m in metrics.values()) / len(metrics)
        return {
            "average_transcription_time": avg_time,
            "tests_completed": len(metrics)
        }
    
    def _summarize_llm_metrics(self, metrics):
        """Summarize LLM metrics"""
        if not metrics:
            return {"status": "No data"}
        
        summary = {}
        for agent_id, agent_metrics in metrics.items():
            avg_time = sum(m["generation_time_seconds"] for m in agent_metrics.values()) / len(agent_metrics)
            avg_length = sum(m["response_length"] for m in agent_metrics.values()) / len(agent_metrics)
            summary[agent_id] = {
                "average_generation_time": avg_time,
                "average_response_length": avg_length,
                "tests_completed": len(agent_metrics)
            }
        
        return summary
    
    def _summarize_turn_metrics(self, metrics):
        """Summarize turn-taking metrics"""
        if not metrics or "statistics" not in metrics:
            return {"status": "No data"}
        
        # Count correct turn predictions
        turn_keys = [k for k in metrics.keys() if k.startswith("turn_")]
        correct_turns = sum(1 for k in turn_keys if metrics[k]["match"])
        
        return {
            "correct_turn_predictions": correct_turns,
            "total_turn_predictions": len(turn_keys),
            "accuracy": correct_turns / len(turn_keys) if turn_keys else 0,
            "statistics": metrics["statistics"]
        }
    
    def _summarize_audio_metrics(self, metrics):
        """Summarize audio routing metrics"""
        if not metrics:
            return {"status": "No data"}
        
        summary = {
            "input_device_found": metrics["input_device"] is not None,
            "output_device_found": metrics["output_device"] is not None,
            "available_device_count": len(metrics["available_devices"])
        }
        
        if "playback_test" in metrics:
            summary["playback_test_completed"] = True
            summary["playback_time"] = metrics["playback_test"]["playback_time_seconds"]
        else:
            summary["playback_test_completed"] = False
        
        return summary
    
    def _generate_html_report(self, summary, output_path):
        """Generate HTML report from summary metrics"""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Multi-Voice Agent System Evaluation Report</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                }
                h1, h2, h3 {
                    color: #2c3e50;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                }
                .section {
                    margin-bottom: 30px;
                    padding: 20px;
                    background-color: #f9f9f9;
                    border-radius: 5px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }
                th, td {
                    padding: 12px 15px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }
                th {
                    background-color: #f2f2f2;
                }
                .metric-good {
                    color: #27ae60;
                }
                .metric-average {
                    color: #f39c12;
                }
                .metric-poor {
                    color: #e74c3c;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Multi-Voice Agent System Evaluation Report</h1>
                <p>This report provides performance metrics for the multi-voice agent system components.</p>
        """
        
        # TTS Section
        html += """
                <div class="section">
                    <h2>Text-to-Speech Performance</h2>
                    <table>
                        <tr>
                            <th>Agent</th>
                            <th>Average Generation Time (s)</th>
                            <th>Tests Completed</th>
                        </tr>
        """
        
        for agent_id, metrics in summary["tts_summary"].items():
            if isinstance(metrics, dict) and "average_generation_time" in metrics:
                time_class = "metric-good" if metrics["average_generation_time"] < 1.0 else "metric-average"
                html += f"""
                        <tr>
                            <td>{agent_id}</td>
                            <td class="{time_class}">{metrics["average_generation_time"]:.2f}</td>
                            <td>{metrics["tests_completed"]}</td>
                        </tr>
                """
        
        html += """
                    </table>
                </div>
        """
        
        # STT Section
        html += """
                <div class="section">
                    <h2>Speech-to-Text Performance</h2>
        """
        
        if isinstance(summary["stt_summary"], dict) and "average_transcription_time" in summary["stt_summary"]:
            time_class = "metric-good" if summary["stt_summary"]["average_transcription_time"] < 2.0 else "metric-average"
            html += f"""
                    <p>Average Transcription Time: <span class="{time_class}">{summary["stt_summary"]["average_transcription_time"]:.2f} seconds</span></p>
                    <p>Tests Completed: {summary["stt_summary"]["tests_completed"]}</p>
            """
        else:
            html += """
                    <p>No STT evaluation data available.</p>
            """
        
        html += """
                </div>
        """
        
        # LLM Section
        html += """
                <div class="section">
                    <h2>LLM Performance</h2>
                    <table>
                        <tr>
                            <th>Agent</th>
                            <th>Average Generation Time (s)</th>
                            <th>Average Response Length</th>
                            <th>Tests Completed</th>
                        </tr>
        """
        
        for agent_id, metrics in summary["llm_summary"].items():
            if isinstance(metrics, dict) and "average_generation_time" in metrics:
                time_class = "metric-good" if metrics["average_generation_time"] < 3.0 else "metric-average"
                html += f"""
                        <tr>
                            <td>{agent_id}</td>
                            <td class="{time_class}">{metrics["average_generation_time"]:.2f}</td>
                            <td>{metrics["average_response_length"]:.0f}</td>
                            <td>{metrics["tests_completed"]}</td>
                        </tr>
                """
        
        html += """
                    </table>
                </div>
        """
        
        # Turn-taking Section
        html += """
                <div class="section">
                    <h2>Turn-Taking Performance</h2>
        """
        
        if isinstance(summary["turn_summary"], dict) and "accuracy" in summary["turn_summary"]:
            accuracy = summary["turn_summary"]["accuracy"]
            accuracy_class = "metric-good" if accuracy > 0.8 else "metric-average" if accuracy > 0.6 else "metric-poor"
            html += f"""
                    <p>Turn Prediction Accuracy: <span class="{accuracy_class}">{accuracy:.2%}</span></p>
                    <p>Correct Predictions: {summary["turn_summary"]["correct_turn_predictions"]} / {summary["turn_summary"]["total_turn_predictions"]}</p>
            """
            
            if "statistics" in summary["turn_summary"]:
                stats = summary["turn_summary"]["statistics"]
                html += f"""
                    <h3>Turn Statistics</h3>
                    <p>Total Turns: {stats.get("total_turns", 0)}</p>
                    <p>Agent Turns: {stats.get("agent_turns", 0)}</p>
                    <p>Audience Turns: {stats.get("audience_turns", 0)}</p>
                    <p>Average Turn Duration: {stats.get("avg_turn_duration", 0):.2f} seconds</p>
                """
        else:
            html += """
                    <p>No turn-taking evaluation data available.</p>
            """
        
        html += """
                </div>
        """
        
        # Audio Routing Section
        html += """
                <div class="section">
                    <h2>Audio Routing Performance</h2>
        """
        
        if isinstance(summary["audio_summary"], dict):
            input_class = "metric-good" if summary["audio_summary"].get("input_device_found", False) else "metric-poor"
            output_class = "metric-good" if summary["audio_summary"].get("output_device_found", False) else "metric-poor"
            
            html += f"""
                    <p>Input Device Found: <span class="{input_class}">{summary["audio_summary"].get("input_device_found", False)}</span></p>
                    <p>Output Device Found: <span class="{output_class}">{summary["audio_summary"].get("output_device_found", False)}</span></p>
                    <p>Available Devices: {summary["audio_summary"].get("available_device_count", 0)}</p>
            """
            
            if summary["audio_summary"].get("playback_test_completed", False):
                playback_time = summary["audio_summary"].get("playback_time", 0)
                time_class = "metric-good" if playback_time < 1.0 else "metric-average"
                html += f"""
                    <p>Playback Test: <span class="metric-good">Completed</span></p>
                    <p>Playback Time: <span class="{time_class}">{playback_time:.2f} seconds</span></p>
                """
            else:
                html += """
                    <p>Playback Test: <span class="metric-poor">Not Completed</span></p>
                """
        else:
            html += """
                    <p>No audio routing evaluation data available.</p>
            """
        
        html += """
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(output_path, "w") as f:
            f.write(html)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Multi-Voice Agent System Evaluator')
    parser.add_argument('--config', default='./config', help='Configuration directory')
    parser.add_argument('--component', choices=['tts', 'stt', 'llm', 'turn', 'audio', 'all'], 
                        default='all', help='Component to evaluate')
    
    args = parser.parse_args()
    
    evaluator = Evaluator(config_dir=args.config)
    
    if args.component == 'tts':
        evaluator.evaluate_tts_performance()
    elif args.component == 'stt':
        evaluator.evaluate_stt_performance()
    elif args.component == 'llm':
        evaluator.evaluate_llm_performance()
    elif args.component == 'turn':
        evaluator.evaluate_turn_taking()
    elif args.component == 'audio':
        evaluator.evaluate_audio_routing()
    else:
        evaluator.run_all_evaluations()

if __name__ == '__main__':
    main()
