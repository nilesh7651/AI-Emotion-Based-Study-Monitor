"""
Accuracy Testing Utility for Emotion Detector

This script helps you test and calibrate the emotion classifier:
1. Real-time testing with ground truth labels
2. Confusion matrix generation
3. Per-emotion accuracy breakdown
4. Model comparison (FER vs DeepFace)

Usage:
    python test_accuracy.py
"""

import cv2
import numpy as np
import time
import json
import os
from collections import defaultdict
from datetime import datetime

from classifier import create_classifier
from camera import Camera
from config import config

# Emotion labels
EMOTIONS = ['Focused', 'Stressed', 'Bored', 'Distracted']
KEY_MAPPINGS = {
    '1': 'Focused',
    '2': 'Stressed', 
    '3': 'Bored',
    '4': 'Distracted',
    '0': 'No Face'
}


class AccuracyTester:
    """Interactive accuracy testing utility."""
    
    def __init__(self, backend='fer'):
        print(f"\n{'='*60}")
        print("Emotion Detector Accuracy Tester")
        print(f"{'='*60}\n")
        
        print(f"Initializing {backend.upper()} classifier...")
        
        if backend == 'deepface':
            self.classifier = create_classifier(
                backend='deepface',
                smoothing_window=config.smoothing_window,
                confidence_threshold=config.confidence_threshold
            )
        else:
            self.classifier = create_classifier(
                backend='fer',
                use_mtcnn=config.use_mtcnn,
                smoothing_window=config.smoothing_window,
                confidence_threshold=config.confidence_threshold
            )
        
        print("Initializing camera...")
        self.camera = Camera(src=config.camera_index)
        
        # Results storage
        self.predictions = []
        self.ground_truths = []
        self.timestamps = []
        self.raw_emotions_log = []
        
        # Statistics
        self.confusion_matrix = defaultdict(lambda: defaultdict(int))
        self.total_samples = 0
        self.correct_predictions = 0
        
        print("\nReady for testing!")
        print("\nInstructions:")
        print("-" * 40)
        print("Press keys 1-4 to label your current emotion:")
        print("  1 = Focused (neutral/happy)")
        print("  2 = Stressed (angry/fear)")
        print("  3 = Bored (sad/tired)")
        print("  4 = Distracted (surprised/looking away)")
        print("  0 = No Face (for testing)")
        print("  q = Quit and show results")
        print("  r = Reset statistics")
        print("  s = Save results to file")
        print("-" * 40)
    
    def run_interactive_test(self):
        """Run interactive testing session with live feedback."""
        cv2.namedWindow("Accuracy Test", cv2.WINDOW_NORMAL)
        
        while True:
            frame = self.camera.get_frame()
            if frame is None:
                continue
            
            # Get prediction
            box, emotions, predicted_state = self.classifier.analyze_frame(frame)
            
            # Draw face box
            if box is not None:
                x, y, w, h = box
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw prediction
            cv2.putText(frame, f"Predicted: {predicted_state}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Draw emotion bars
            if emotions:
                y_offset = 60
                for emotion, score in emotions.items():
                    # Normalize score (some backends return 0-100, others 0-1)
                    if score > 1:
                        score = score / 100
                    bar_width = int(score * 200)
                    cv2.rectangle(frame, (10, y_offset), (10 + bar_width, y_offset + 15), 
                                (0, 255, 0), -1)
                    cv2.putText(frame, f"{emotion}: {score:.2f}", (220, y_offset + 12),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    y_offset += 20
            
            # Draw instructions
            h, w = frame.shape[:2]
            cv2.putText(frame, "Press 1-4 to label | q=quit | r=reset | s=save", 
                       (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Draw accuracy
            if self.total_samples > 0:
                accuracy = (self.correct_predictions / self.total_samples) * 100
                cv2.putText(frame, f"Accuracy: {accuracy:.1f}% ({self.correct_predictions}/{self.total_samples})",
                           (10, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            cv2.imshow("Accuracy Test", frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('r'):
                self._reset_stats()
                print("\nStatistics reset!")
            elif key == ord('s'):
                self._save_results()
            elif chr(key) in KEY_MAPPINGS:
                ground_truth = KEY_MAPPINGS[chr(key)]
                self._record_sample(predicted_state, ground_truth, emotions)
        
        cv2.destroyAllWindows()
        self.camera.release()
        
        self._show_results()
    
    def _record_sample(self, predicted, ground_truth, emotions):
        """Record a sample with prediction and ground truth."""
        self.predictions.append(predicted)
        self.ground_truths.append(ground_truth)
        self.timestamps.append(datetime.now().isoformat())
        self.raw_emotions_log.append(emotions)
        
        self.confusion_matrix[ground_truth][predicted] += 1
        self.total_samples += 1
        
        if predicted == ground_truth:
            self.correct_predictions += 1
            print(f"✓ Correct: {predicted}")
        else:
            print(f"✗ Wrong: predicted={predicted}, actual={ground_truth}")
    
    def _reset_stats(self):
        """Reset all statistics."""
        self.predictions.clear()
        self.ground_truths.clear()
        self.timestamps.clear()
        self.raw_emotions_log.clear()
        self.confusion_matrix.clear()
        self.total_samples = 0
        self.correct_predictions = 0
    
    def _show_results(self):
        """Display comprehensive accuracy results."""
        print("\n" + "=" * 60)
        print("ACCURACY TEST RESULTS")
        print("=" * 60)
        
        if self.total_samples == 0:
            print("No samples recorded.")
            return
        
        # Overall accuracy
        accuracy = (self.correct_predictions / self.total_samples) * 100
        print(f"\nOverall Accuracy: {accuracy:.1f}%")
        print(f"Correct: {self.correct_predictions} / Total: {self.total_samples}")
        
        # Per-class accuracy
        print("\n" + "-" * 40)
        print("Per-Class Accuracy:")
        print("-" * 40)
        
        all_labels = set(self.ground_truths) | set(self.predictions)
        
        for label in sorted(all_labels):
            correct = self.confusion_matrix[label][label]
            total = sum(self.confusion_matrix[label].values())
            if total > 0:
                class_acc = (correct / total) * 100
                print(f"  {label:15s}: {class_acc:6.1f}% ({correct}/{total})")
            else:
                print(f"  {label:15s}: No samples")
        
        # Confusion matrix
        print("\n" + "-" * 40)
        print("Confusion Matrix (rows=actual, cols=predicted):")
        print("-" * 40)
        
        labels = sorted(all_labels)
        header = "Actual\\Pred  " + "  ".join([f"{l[:8]:>8}" for l in labels])
        print(header)
        print("-" * len(header))
        
        for actual in labels:
            row = f"{actual[:12]:12s}"
            for predicted in labels:
                count = self.confusion_matrix[actual][predicted]
                row += f"  {count:8d}"
            print(row)
        
        # Common misclassifications
        print("\n" + "-" * 40)
        print("Common Misclassifications:")
        print("-" * 40)
        
        misclass = []
        for actual in labels:
            for predicted in labels:
                if actual != predicted and self.confusion_matrix[actual][predicted] > 0:
                    misclass.append((actual, predicted, self.confusion_matrix[actual][predicted]))
        
        misclass.sort(key=lambda x: x[2], reverse=True)
        for actual, predicted, count in misclass[:5]:
            print(f"  {actual} → {predicted}: {count} times")
    
    def _save_results(self):
        """Save results to JSON file."""
        filename = f"accuracy_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        results = {
            "test_date": datetime.now().isoformat(),
            "model_backend": config.model_backend,
            "use_mtcnn": config.use_mtcnn,
            "smoothing_window": config.smoothing_window,
            "confidence_threshold": config.confidence_threshold,
            "total_samples": self.total_samples,
            "correct_predictions": self.correct_predictions,
            "accuracy_percent": (self.correct_predictions / self.total_samples * 100) if self.total_samples > 0 else 0,
            "confusion_matrix": {k: dict(v) for k, v in self.confusion_matrix.items()},
            "predictions": self.predictions,
            "ground_truths": self.ground_truths,
            "timestamps": self.timestamps
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to: {filename}")


def run_benchmark(n_frames=100):
    """
    Benchmark both classifiers for speed and compare predictions.
    """
    print("\n" + "=" * 60)
    print("CLASSIFIER BENCHMARK")
    print("=" * 60)
    
    camera = Camera(src=config.camera_index)
    
    # Test FER
    print("\nTesting FER classifier...")
    fer_classifier = create_classifier(backend='fer', use_mtcnn=True)
    fer_times = []
    fer_predictions = []
    
    for i in range(n_frames):
        frame = camera.get_frame()
        if frame is None:
            continue
        
        start = time.time()
        box, emotions, state = fer_classifier.analyze_frame(frame)
        fer_times.append(time.time() - start)
        fer_predictions.append(state)
        
        if (i + 1) % 20 == 0:
            print(f"  Progress: {i + 1}/{n_frames}")
    
    # Test DeepFace
    print("\nTesting DeepFace classifier...")
    df_classifier = create_classifier(backend='deepface')
    df_times = []
    df_predictions = []
    
    # Reset camera position
    camera.release()
    camera = Camera(src=config.camera_index)
    
    for i in range(n_frames):
        frame = camera.get_frame()
        if frame is None:
            continue
        
        start = time.time()
        box, emotions, state = df_classifier.analyze_frame(frame)
        df_times.append(time.time() - start)
        df_predictions.append(state)
        
        if (i + 1) % 20 == 0:
            print(f"  Progress: {i + 1}/{n_frames}")
    
    camera.release()
    
    # Results
    print("\n" + "-" * 40)
    print("BENCHMARK RESULTS")
    print("-" * 40)
    
    print(f"\nFER Classifier:")
    print(f"  Avg time per frame: {np.mean(fer_times)*1000:.1f} ms")
    print(f"  Max time: {np.max(fer_times)*1000:.1f} ms")
    print(f"  FPS: {1/np.mean(fer_times):.1f}")
    
    print(f"\nDeepFace Classifier:")
    print(f"  Avg time per frame: {np.mean(df_times)*1000:.1f} ms")
    print(f"  Max time: {np.max(df_times)*1000:.1f} ms")
    print(f"  FPS: {1/np.mean(df_times):.1f}")
    
    # Agreement
    agreement = sum(1 for f, d in zip(fer_predictions, df_predictions) if f == d)
    print(f"\nClassifier Agreement: {agreement}/{len(fer_predictions)} ({agreement/len(fer_predictions)*100:.1f}%)")


def quick_test():
    """
    Quick test with 10 frames to verify classifier is working.
    """
    print("\n" + "=" * 60)
    print("QUICK CLASSIFIER TEST")
    print("=" * 60)
    
    camera = Camera(src=config.camera_index)
    classifier = create_classifier(
        backend=config.model_backend,
        use_mtcnn=config.use_mtcnn if config.model_backend == 'fer' else None,
        smoothing_window=config.smoothing_window,
        confidence_threshold=config.confidence_threshold
    )
    
    print(f"\nModel: {config.model_backend}")
    print(f"MTCNN: {config.use_mtcnn}")
    print(f"Smoothing: {config.smoothing_window} frames")
    print(f"Confidence threshold: {config.confidence_threshold}")
    print("\nRunning 10 test frames...")
    
    for i in range(10):
        frame = camera.get_frame()
        if frame is None:
            print(f"  Frame {i+1}: No frame captured")
            continue
        
        start = time.time()
        box, emotions, state = classifier.analyze_frame(frame)
        elapsed = (time.time() - start) * 1000
        
        if emotions:
            # Get top emotion
            if isinstance(list(emotions.values())[0], float) and max(emotions.values()) <= 1:
                top_emotion = max(emotions.items(), key=lambda x: x[1])
                print(f"  Frame {i+1}: {state:15s} | Top: {top_emotion[0]}={top_emotion[1]:.2f} | {elapsed:.0f}ms")
            else:
                top_emotion = max(emotions.items(), key=lambda x: x[1])
                print(f"  Frame {i+1}: {state:15s} | Top: {top_emotion[0]}={top_emotion[1]:.0f}% | {elapsed:.0f}ms")
        else:
            print(f"  Frame {i+1}: {state:15s} | {elapsed:.0f}ms")
        
        time.sleep(0.3)
    
    camera.release()
    print("\nQuick test complete!")


if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 60)
    print("EMOTION DETECTOR ACCURACY TESTING")
    print("=" * 60)
    print("\nOptions:")
    print("  1. Interactive Test (label emotions in real-time)")
    print("  2. Quick Test (10 frames)")
    print("  3. Benchmark (compare FER vs DeepFace)")
    print("  q. Quit")
    
    choice = input("\nEnter choice (1/2/3/q): ").strip()
    
    if choice == '1':
        backend = input("Choose backend (fer/deepface) [fer]: ").strip() or 'fer'
        tester = AccuracyTester(backend=backend)
        tester.run_interactive_test()
    elif choice == '2':
        quick_test()
    elif choice == '3':
        n = input("Number of frames per classifier [100]: ").strip()
        n_frames = int(n) if n else 100
        run_benchmark(n_frames)
    else:
        print("Goodbye!")
