import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QPen, QBrush
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QRectF

class OverlayHUD(QWidget):
    # Define state colors
    COLORS = {
        'IDLE': QColor('#64748b'),       # Muted Gray
        'LISTENING': QColor('#06b6d4'),  # Teal
        'RETRIEVING': QColor('#eab308'), # Yellow/gold
        'SPEAKING': QColor('#22c55e'),   # Green
    }

    def __init__(self, parent=None):
        # Without this call to the parent constructor, calling Qt methods on self would cause a runtime error 
        super().__init__(parent)
        
        self.setFixedSize(120, 120)
        
        # Window flags so that the script will run independently of the game
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.Tool
        )
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Current state
        self._current_state = 'IDLE'
        # IDLE state variables
        self._phase_angle = 0.0
        # LISTENING state variables
        self._wave_radii = [30.0, 30.0, 30.0]
        self._wave_alphas = [0.0, 0.0, 0.0]
        # RETRIEVING state variables
        self._orbit_angle = 0.0
        # SPEAKING state variables
        self._pulse_alpha = 255.0
        self._pulse_increasing = False

        # Animation timer (~16ms = 60 FPS)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_animation)
        self._timer.start(16)

    @pyqtSlot(str)
    def set_state(self, state: str):
        if state not in self.COLORS:
            return
            
        if self._current_state != state:
            self._current_state = state
            # Reset animations slightly for a smooth transition (staggered between min 25.0 and max 55.0)
            self._wave_radii = [25.0, 35.0, 45.0]
            self._wave_alphas = [1.0, 0.66, 0.33]

    def _update_animation(self):
        """Updates animation based on state."""
        # Orbit rotation for RETRIEVING
        self._orbit_angle = (self._orbit_angle + 3.0) % 360.0
        
        # Idle slow pulse
        if self._current_state == 'IDLE':
            pulse_speed = 2.0
            if self._pulse_increasing:
                self._pulse_alpha += pulse_speed
                if self._pulse_alpha >= 255:
                    self._pulse_alpha = 255
                    self._pulse_increasing = False
            else:
                self._pulse_alpha -= pulse_speed
                if self._pulse_alpha <= 100:
                    self._pulse_alpha = 100
                    self._pulse_increasing = True
        
        # Wave expansion for LISTENING and SPEAKING
        if self._current_state in ('LISTENING', 'SPEAKING'):
            expansion_speed = 0.5 if self._current_state == 'LISTENING' else 1.5
            max_radius = 55.0
            min_radius = 25.0
            
            for i in range(len(self._wave_radii)):
                self._wave_radii[i] += expansion_speed
                
                # Update alpha based on radius (decays as it expands)
                progress = (self._wave_radii[i] - min_radius) / (max_radius - min_radius)
                self._wave_alphas[i] = max(0.0, 1.0 - progress)
                
                # Reset wave if it expands too far
                if self._wave_radii[i] >= max_radius:
                    self._wave_radii[i] = min_radius
                    self._wave_alphas[i] = 1.0

        # Trigger a repaint
        self.update()

    def paintEvent(self, event):
        """Draws the HUD."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        center = self.rect().center()
        
        base_color = self.COLORS[self._current_state]
        
        # 1. Outer Wave Rings (LISTENING / SPEAKING)
        if self._current_state in ('LISTENING', 'SPEAKING'):
            for i in range(len(self._wave_radii)):
                if self._wave_alphas[i] > 0:
                    radius = self._wave_radii[i]
                    wave_color = QColor(base_color)
                    wave_color.setAlphaF(self._wave_alphas[i] * 0.8) # max 80% opacity for rings
                    
                    pen = QPen(wave_color, 2.0)
                    painter.setPen(pen)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawEllipse(center, int(radius), int(radius))

        # 2. Orbit Ring (RETRIEVING)
        if self._current_state == 'RETRIEVING':
            radius = 35.0
            orbit_color = QColor(base_color)
            
            pen = QPen(orbit_color, 3.0, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            painter.translate(center)
            painter.rotate(self._orbit_angle)
            painter.drawEllipse(-int(radius), -int(radius), int(radius*2), int(radius*2))
            painter.rotate(-self._orbit_angle)
            painter.translate(-center)

        # 3. Center Node
        node_radius = 25.0
        
        # Background of the center node
        bg_color = QColor(15, 23, 42, 200) # Dark semi-transparent
        painter.setBrush(QBrush(bg_color))
        
        # Border of the center node
        border_color = QColor(base_color)
        if self._current_state == 'IDLE':
            border_color.setAlpha(int(self._pulse_alpha))
            
        border_pen = QPen(border_color, 2.0)
        painter.setPen(border_pen)
        painter.drawEllipse(center, int(node_radius), int(node_radius))

        # 4. Mic Icon (Vector drawn)
        # Shifted slightly (-0.75px horizontally, -3px vertically) for optical centering
        self._draw_mic_icon(painter, center_x - 0.75, center_y - 3.0, border_color)
        
    def _draw_mic_icon(self, painter: QPainter, cx: float, cy: float, color: QColor):
        """Draws a central microphone icon using QPainterPath."""
        painter.setPen(QPen(color, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Scale down slightly to fit the center node
        scale = 0.6
        
        # Capsule
        capsule_width = 12 * scale
        capsule_height = 24 * scale
        
        capsule_rect = QRectF(
            cx - capsule_width / 2,
            cy - capsule_height / 2 - 2 * scale,
            capsule_width,
            capsule_height
        )
        painter.drawRoundedRect(capsule_rect, capsule_width / 2, capsule_width / 2)
        
        # Stand / curved bottom
        path = QPainterPath()
        stand_radius = 12 * scale
        stand_start_x = cx - stand_radius
        stand_start_y = cy + 2 * scale
        
        # Draw the arc for the cup
        path.moveTo(stand_start_x, stand_start_y)
        path.arcTo(stand_start_x, stand_start_y - stand_radius, stand_radius * 2, stand_radius * 2, 180, 180)
        
        # Draw the stem
        path.moveTo(cx, stand_start_y + stand_radius)
        path.lineTo(cx, stand_start_y + stand_radius + 6 * scale)
        
        # Draw the base
        path.moveTo(cx - 6 * scale, stand_start_y + stand_radius + 6 * scale)
        path.lineTo(cx + 6 * scale, stand_start_y + stand_radius + 6 * scale)
        
        painter.drawPath(path)
