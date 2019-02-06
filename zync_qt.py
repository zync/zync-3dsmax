"""Contains adapters to Qt Widgets."""
try:
  import pysideuic

  from PySide.QtCore import QThread
  from PySide.QtCore import Qt
  from PySide.QtCore import Signal
  from PySide.QtCore import QSize
  from PySide.QtGui import QDialog
  from PySide.QtGui import QIntValidator
  from PySide.QtGui import QMessageBox
  from PySide.QtGui import QMovie
  from PySide.QtGui import QWidget
except ImportError:
  import pyside2uic as pysideuic

  from PySide2.QtCore import QThread
  from PySide2.QtCore import Qt
  from PySide2.QtCore import Signal
  from PySide2.QtCore import QSize
  from PySide2.QtGui import QIntValidator
  from PySide2.QtGui import QMovie
  from PySide2.QtWidgets import QDialog
  from PySide2.QtWidgets import QMessageBox
  from PySide2.QtWidgets import QWidget


def create_movie_widget(movie_path, width, height):
  movie = QMovie(movie_path)
  movie.setScaledSize(QSize(width, height))
  return movie


class QtWidgetAdapter(object):
  """Base adapter to Qt widgets."""

  def __init__(self, widget):
    self._widget = widget

  @property
  def enabled(self):
    """Gets or sets the enable state of the widget"""
    return self._widget.isEnabled()

  @enabled.setter
  def enabled(self, enabled):
    self._widget.setEnabled(enabled)


class QtButtonAdapter(QtWidgetAdapter):
  """Adapter to Qt button widget."""

  def __init__(self, widget):
    super(QtButtonAdapter, self).__init__(widget)

  def set_on_clicked(self, on_clicked):
    if on_clicked is not None:
      self._widget.clicked.connect(on_clicked)


class QtCheckboxAdapter(QtWidgetAdapter):
  """Adapter to Qt checkbox and radio button widgets."""

  def __init__(self, widget):
    super(QtCheckboxAdapter, self).__init__(widget)

  def set_on_checked(self, on_checked):
    if on_checked is not None:

      def handle_clicked():
        on_checked(self.checked)

      self._widget.clicked.connect(handle_clicked)

  @property
  def checked(self):
    """Gets or sets the checked state of the checkbox/radio button."""
    return self._widget.isChecked()

  @checked.setter
  def checked(self, checked):
    self._widget.setChecked(checked)


class QtComboboxAdapter(QtWidgetAdapter):
  """Adapter to Qt combobox widget."""

  def __init__(self, widget):
    super(QtComboboxAdapter, self).__init__(widget)

  def set_on_changed(self, on_changed):
    if on_changed is not None:

      def handle_changed():
        on_changed(self._widget.currentText())

      self._widget.currentIndexChanged.connect(handle_changed)

  def contains_element(self, element):
    """Tests if the widget contains an element."""
    for i in range(self._widget.count()):
      current_element = self._widget.itemText(i)
      if current_element == element:
        return True
    return False

  def populate(self, elements):
    """Populates the widget with elements."""
    self._widget.clear()
    for element in elements:
      self._widget.addItem(element)
    if self._widget.count() > 0:
      self._widget.setCurrentIndex(0)

  @property
  def selected_element(self):
    """Gets or sets the element selected in the widget.

    Raises:
      ValueError: when set to element that is not contained by the widget.
    """
    return self._widget.currentText()

  @selected_element.setter
  def selected_element(self, element):
    for i in range(self._widget.count()):
      current_element = self._widget.itemText(i)
      if current_element == element:
        self._widget.setCurrentIndex(i)
        return
    raise ValueError("Widget doesn't contain element %s" % element)


class QtDialogAdapter(QtWidgetAdapter):
  """Adapter to Qt dialog."""

  def __init__(self, dialog):
    super(QtDialogAdapter, self).__init__(dialog)
    self._dialog = dialog

  def close(self):
    self._dialog.close()

  def show(self, caption=None):
    if caption is not None:
      self._dialog.setWindowTitle(caption)
    self._dialog.show()

  def get_button(self, name):
    return QtButtonAdapter(self._get_widget(name))

  def get_checkbox(self, name):
    return QtCheckboxAdapter(self._get_widget(name))

  def get_combobox(self, name):
    return QtComboboxAdapter(self._get_widget(name))

  def get_label(self, name):
    return QtLabelAdapter(self._get_widget(name))

  def get_numerical_field(self, name):
    return QtNumericalFieldAdapter(self._get_widget(name))

  def get_text_field(self, name):
    return QtTextFieldAdapter(self._get_widget(name))

  def _get_widget(self, name):
    return getattr(self._dialog, name)


class QtLabelAdapter(QtWidgetAdapter):
  """Adapter to Qt label widget."""

  def __init__(self, widget):
    super(QtLabelAdapter, self).__init__(widget)

  @property
  def text(self):
    return self._widget.text()

  @text.setter
  def text(self, text):
    self._widget.setText(text)


class QtNumericalFieldAdapter(QtWidgetAdapter):
  """Adapter to Qt line edit widget with int validator."""

  def __init__(self, widget):
    super(QtNumericalFieldAdapter, self).__init__(widget)

  def set_on_changed(self, on_changed):
    if on_changed is not None:

      def handle_changed():
        try:
          value = int(self._widget.text())
          on_changed(value)
        except ValueError:
          pass

      self._widget.textChanged.connect(handle_changed)

  def set_validation(self, min_value, max_value):
    self._widget.setValidator(QIntValidator(min_value, max_value))

  @property
  def value(self):
    """Gets or sets the content of the widget."""
    return int(self._widget.text())

  @value.setter
  def value(self, value):
    self._widget.setText(str(value))


class QtTextFieldAdapter(QtWidgetAdapter):
  """Adapter to Qt line edit widget."""

  def __init__(self, widget):
    super(QtTextFieldAdapter, self).__init__(widget)

  def set_on_changed(self, on_changed):
    if on_changed is not None:

      def handle_changed():
        on_changed(self._widget.text())

      self._widget.textChanged.connect(handle_changed)

  @property
  def text(self):
    """Gets or sets the content of the widget."""
    return self._widget.text()

  @text.setter
  def text(self, text):
    self._widget.setText(text)


class QtAsyncThread(QThread):
  """Wrapper to Qt new_thread."""
  signal_succeeded = Signal(object)
  signal_failed = Signal(Exception)

  threads = []

  def __init__(self, thread_func, success_callback, failure_callback):
    """Class constructor.

    Args:
      thread_func: parameterless function to be executed in a new_thread
      success_callback: callback to be called when the new_thread ends without
        errors, the result of thread_func is passed as an argument
      failure_callback: callback to be called when the new_thread ends with an
        error, the exception is passed as an argument.
    """
    super(QtAsyncThread, self).__init__()
    self._func = thread_func
    self._on_success = success_callback
    self._on_failure = failure_callback

    self.signal_succeeded.connect(self._wrap_callback(success_callback))
    self.signal_failed.connect(self._wrap_callback(failure_callback))
    QtAsyncThread.threads.append(self)

  def _wrap_callback(self, callback):

    def wrapper(result):
      try:
        if callback is not None:
          callback(result)
      finally:
        QtAsyncThread.threads.remove(self)

    return wrapper

  def run(self):
    """Runs the thread.

    If exception is thrown, it is passed to on_failure callback. Otherwise,
    on_success callback is called with a result of the thread function.

    If thread function returns None, object() is passed.
    """
    try:
      result = self._func()
      if result is None:
        result = object()
      self.signal_succeeded.emit(result)
    except Exception as e:
      self.signal_failed.emit(e)


class QtGuiUtils(object):

  @staticmethod
  def new_thread(runner, on_success, on_failure):
    """Creates a new_thread."""
    return QtAsyncThread(runner, on_success, on_failure)

  @staticmethod
  def show_error_message_box(message):
    """Displays a message box with error message."""
    QMessageBox.critical(None, 'Error', message)

  @staticmethod
  def show_info_message_box(message):
    """Displays a message box with info message."""
    QMessageBox.information(None, '', message)
