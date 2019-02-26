import sys
from unittest import TestCase

from zync_model.scanline_model import ScanlineModel
from zync_model.vray_model import VrayModel
from zync_presenter import Presenter


class WidgetMock(object):

  def __init__(self):
    self.enabled = True


class ButtonMock(WidgetMock):

  def __init__(self):
    super(ButtonMock, self).__init__()
    self._on_clicked = None

  def set_on_clicked(self, on_clicked):
    self._on_clicked = on_clicked

  def click(self):
    if self._on_clicked is not None:
      self._on_clicked()


class CheckboxMock(WidgetMock):

  def __init__(self):
    super(CheckboxMock, self).__init__()
    self._on_checked = None
    self._checked = False

  def set_on_checked(self, on_checked):
    self._on_checked = on_checked

  @property
  def checked(self):
    return self._checked

  @checked.setter
  def checked(self, checked):
    if self._checked != checked:
      self._checked = checked
      if self._on_checked is not None:
        self._on_checked(self._checked)


class ComboboxMock(WidgetMock):

  def __init__(self):
    super(ComboboxMock, self).__init__()
    self._on_changed = None
    self._selected_index = -1
    self.elements = []

  def set_on_changed(self, on_changed):
    self._on_changed = on_changed

  def contains_element(self, element):
    return element in self.elements

  def populate(self, elements):
    self.elements = elements
    if len(elements) > 0:
      self._set_selected_index(0)
    else:
      self._set_selected_index(-1)

  @property
  def selected_element(self):
    return self.elements[self._selected_index]

  @selected_element.setter
  def selected_element(self, element):
    for index, current_element in enumerate(self.elements):
      if current_element == element:
        self._set_selected_index(index)
        return
    raise ValueError("Widget doesn't contain element %s" % element)

  def _set_selected_index(self, index):
    if self._selected_index != index:
      self._selected_index = index
      if self._on_changed is not None:
        if 0 <= index < len(self.elements):
          self._on_changed(self.elements[index])
        else:
          self._on_changed('')


class DialogMock(object):

  def __init__(self):
    self._caption = None
    self._visible = False

  def close(self):
    self._visible = False

  def show(self, caption=None):
    if caption is not None:
      self._caption = caption
    self._visible = True

  @property
  def caption(self):
    return self._caption

  @property
  def visible(self):
    return self._visible

  def get_button(self, _):
    return ButtonMock()

  def get_checkbox(self, _):
    return CheckboxMock()

  def get_combobox(self, _):
    return ComboboxMock()

  def get_label(self, _):
    return LabelMock()

  def get_numerical_field(self, _):
    return NumericalFieldMock()

  def get_text_field(self, _):
    return TextFieldMock()


class LabelMock(WidgetMock):

  def __init__(self):
    super(LabelMock, self).__init__()
    self.text = ''


class NumericalFieldMock(WidgetMock):

  def __init__(self):
    super(NumericalFieldMock, self).__init__()
    self._max = sys.maxint
    self._min = 0
    self._on_changed = None
    self._value = None

  def set_on_changed(self, on_changed):
    self._on_changed = on_changed

  @property
  def value(self):
    if self._value is not None:
      return self._value
    raise ValueError()

  @value.setter
  def value(self, value):
    if self._min <= value <= self._max:
      self._value = value
      if self._on_changed is not None:
        self._on_changed(value)

  def set_validation(self, min_value, max_value):
    self._min = min_value
    self._max = max_value


class TextFieldMock(WidgetMock):

  def __init__(self):
    super(TextFieldMock, self).__init__()
    self._on_changed = None
    self._text = ''

  def set_on_changed(self, on_changed):
    self._on_changed = on_changed

  @property
  def text(self):
    return self._text

  @text.setter
  def text(self, text):
    self._text = text
    if self._on_changed is not None:
      self._on_changed(self._text)


class ThreadMock(object):
  threads = []

  def __init__(self, func, on_success, on_failure):
    self._func = func
    self._on_success = on_success
    self._on_failure = on_failure

  def start(self):
    try:
      result = self._func()
      if self._on_success is not None:
        self._on_success(result)
    except Exception as e:
      if self._on_failure is not None:
        self._on_failure(e)


class GuiUtilsMock(object):

  def __init__(self):
    self.last_error_message = None
    self.last_info_message = None

  def show_error_message_box(self, message):
    self.last_error_message = message

  def show_info_message_box(self, message):
    self.last_info_message = message

  def new_thread(self, runner, on_success, on_failure):
    return ThreadMock(runner, on_success, on_failure)


class MaxApiMock(object):

  def __init__(self):
    self.assets = ['C:/asset1.png', 'C:/Path/asset2.abc']
    self.camera_names = ['Camera1', 'Camera2']
    self.frame_range = '1-100'
    self.is_save_pending = False
    self.max_version = '2018.4'
    self.output_dir_name = 'C:/Output/'
    self.output_file_name = 'C:/Output/output.exr'
    self.project_path = 'C:/Project/Path'
    self.resolution = (1920, 1080)
    self.scene_file_name = 'test_scene.max'
    self.scene_file_path = 'C:/test_scene.max'
    self.xrefs = ['C:/xref1.max', 'C:/xref2.max']


class ZyncApiMock(object):

  def __init__(self):
    self.selected_files = {}
    self.submitted_arguments = None

  def estimated_cost(self, instance_type_label, renderer_type, instance_count):
    return str(instance_count * 10)

  def get_existing_project_names(self):
    return ['Project1', 'Project2']

  def is_renderer_available_as_standalone(self, renderer_name):
    return False

  def is_renderer_available_as_non_standalone(self, renderer_name):
    return True

  def instance_type(self, instance_type_label, renderer_type):
    return instance_type_label + '_' + renderer_type

  def instance_type_labels(self, renderer_type, usage_tag):
    return ['%s_%s_%s' % (renderer_type, usage_tag, num) for num in range(0, 3)]

  def logged_as(self):
    return 'test_user@zync.io'

  def show_selected_files_dialog(self, project_name):
    self.selected_files[project_name] = [
        '%s_%s.png' % (project_name, i) for i in range(0, 3)
    ]

  def get_selected_files(self, project_name):
    if project_name in self.selected_files:
      return self.selected_files[project_name]
    return None

  def submit_job(self, scene_file, params, job_type):
    self.submitted_arguments = [scene_file, params, job_type]

  def is_v2(self):
    return False


class TestPresenter(TestCase):
  """Integration tests for Presenter."""

  def setUp(self):

    self._version = '1.2.3'
    self._user_name = 'test_user'
    self._max_api = MaxApiMock()
    self._zync_api = ZyncApiMock()
    self._model = ScanlineModel()

  def _create_presenter(self,
                        version=None,
                        user_name=None,
                        max_api=None,
                        zync_api=None,
                        model=None):

    class TestPresenter(Presenter):

      def __init__(self, version, default_project_name, max_api, zync_api,
                   model):
        submit_dialog = DialogMock()
        spinner_dialog = DialogMock()
        super(TestPresenter, self).__init__(
            version=version,
            default_project_name=default_project_name,
            max_api=max_api,
            zync_api=zync_api,
            model=model,
            submit_dialog=submit_dialog,
            spinner_dialog=spinner_dialog,
            gui_utils=GuiUtilsMock(),
            thread_provider=ThreadMock)

      @property
      def gui_utils(self):
        return self._gui_utils

    return TestPresenter(
        version=version or self._version,
        default_project_name=user_name or self._user_name,
        max_api=max_api or self._max_api,
        zync_api=zync_api or self._zync_api,
        model=model or self._model)

  def test_should_correctly_initialize_gui_and_model(self):
    # given
    presenter = self._create_presenter()

    # when
    presenter.start()

    # then
    self.assertEqual('1.2.3', self._model.plugin_version)
    self.assertEqual('2018.4', self._model.max_version)
    self.assertEqual(['C:/asset1.png', 'C:/Path/asset2.abc'],
                     self._model.assets)
    self.assertEqual('C:/Project/Path', self._model.project_path)
    self.assertEqual(['C:/xref1.max', 'C:/xref2.max'], self._model.xrefs)
    self.assertEqual(1, self._model.instance_count)
    self.assertEqual(50, self._model.priority)
    self.assertEqual('test_user', self._model.project)
    self.assertEqual('1-100', self._model.frame_range)
    self.assertEqual(1, self._model.frame_step)
    self.assertEqual(10, self._model.chunk_size)
    self.assertEqual(False, self._model.upload_only)
    self.assertEqual(False, self._model.notify_complete)
    self.assertEqual(False, self._model.sync_extra_assets)
    self.assertEqual([], self._model.extra_assets)
    self.assertEqual((1920, 1080), self._model.resolution)
    self.assertEqual('C:/Output/output.exr', self._model.output_name)
    self.assertEqual(['Camera1', 'Camera2'],
                     presenter._camera_names_combo.elements)
    self.assertEqual(10, presenter._chunk_size_field.value)
    self.assertEqual('1-100', presenter._frame_range_field.text)
    self.assertEqual(1, presenter._frame_step_field.value)
    self.assertEqual('C:/Output/output.exr', presenter._output_name_field.text)
    self.assertEqual('Scanline Renderer', presenter._renderer_name_label.text)
    self.assertFalse(presenter._select_files_button.enabled)
    self.assertEqual(1920, presenter._x_resolution_field.value)
    self.assertEqual(1080, presenter._y_resolution_field.value)

  def test_should_guess_output_name_if_not_present_but_scene_file_name_available(
      self):
    # given
    self._max_api.output_file_name = ''
    presenter = self._create_presenter()

    # when
    presenter.start()

    # then
    self.assertEqual('C:/Output/test_scene.exr', self._model.output_name)

  def test_should_guess_output_name_if_not_present_and_no_scene_file_name_available(
      self):
    # given
    self._max_api.output_file_name = ''
    self._max_api.scene_file_name = ''
    presenter = self._create_presenter()

    # when
    presenter.start()

    # then
    self.assertEqual('C:/Output/unknown.exr', self._model.output_name)

  def test_should_leave_output_name_empty_if_cant_be_guessed(self):
    # given
    self._max_api.output_dir_name = ''
    self._max_api.output_file_name = ''
    presenter = self._create_presenter()

    # when
    presenter.start()

    # then
    self.assertEqual('', self._model.output_name)

  def test_should_display_exception_when_scene_not_saved_and_close_spinner_dialog(
      self):
    # given
    self._max_api.is_save_pending = True

    # when
    presenter = self._create_presenter()
    presenter.start()

    # then
    self.assertEqual('Scene needs to be saved before submitting',
                     presenter.gui_utils.last_error_message)
    self.assertFalse(presenter._spinner_dialog.visible)

  def test_should_correctly_initialize_api_dependent_gui_widgets(self):
    # given
    presenter = self._create_presenter()

    # when
    presenter.start()

    # then
    self.assertFalse(presenter._spinner_dialog.visible)
    self.assertFalse(presenter._use_standalone_checkbox.enabled)
    self.assertFalse(presenter._use_standalone_checkbox.checked)
    self.assertEqual(1, presenter._instance_count_field.value)
    self.assertEqual(
        ['scanline_3dsmax_0', 'scanline_3dsmax_1', 'scanline_3dsmax_2'],
        presenter._instance_types_combo.elements)
    self.assertEqual(['Project1', 'Project2'],
                     presenter._existing_project_names_combo.elements)
    self.assertFalse(presenter._existing_project_names_combo.enabled)
    self.assertFalse(presenter._existing_project_checkbox.checked)
    self.assertTrue(presenter._new_project_name_field.enabled)
    self.assertTrue(presenter._new_project_checkbox.checked)
    self.assertEqual('test_user', presenter._new_project_name_field.text)
    self.assertEqual('Logged in as: test_user@zync.io',
                     presenter._logged_as_label.text)
    self.assertTrue(presenter._submit_dialog.visible)
    self.assertEqual('Est. Cost per Hour: 10',
                     presenter._estimated_cost_label.text)

  def test_should_disable_and_uncheck_use_standalone_if_standalone_not_supported(
      self):
    # given
    presenter = self._create_presenter()

    # when
    presenter.start()

    # then
    self.assertFalse(presenter._use_standalone_checkbox.enabled)
    self.assertFalse(presenter._use_standalone_checkbox.checked)

  def test_should_disable_and_check_use_standalone_if_standalone_supported(
      self):
    # given
    presenter = self._create_presenter(
        model=VrayModel('3.60.04', None, None, True))

    # when
    presenter.start()

    # then
    self.assertFalse(presenter._use_standalone_checkbox.enabled)
    self.assertTrue(presenter._use_standalone_checkbox.checked)

  def test_should_select_existing_project_if_matches_the_default_project_name(
      self):
    # given
    presenter = self._create_presenter(user_name='Project1')

    # when
    presenter.start()

    # then
    self.assertFalse(presenter._new_project_checkbox.checked)
    self.assertFalse(presenter._new_project_name_field.enabled)
    self.assertTrue(presenter._existing_project_checkbox.checked)
    self.assertTrue(presenter._existing_project_names_combo.enabled)
    self.assertEqual('Project1',
                     presenter._existing_project_names_combo.selected_element)

  def test_should_disable_existing_projects_fields_when_new_project_name_checked(
      self):
    # given
    presenter = self._create_presenter(user_name='Project1')
    presenter.start()
    # make sure new project fields are initially unchecked / disabled
    self.assertFalse(presenter._new_project_name_field.enabled)
    self.assertFalse(presenter._new_project_checkbox.checked)

    # when
    presenter._new_project_checkbox.checked = True

    # then
    self.assertTrue(presenter._new_project_name_field.enabled)
    self.assertTrue(presenter._new_project_checkbox.checked)
    self.assertFalse(presenter._existing_project_names_combo.enabled)
    self.assertFalse(presenter._existing_project_checkbox.checked)

  def test_should_correctly_update_estimated_cost_and_instance_count_in_model(
      self):
    # given
    presenter = self._create_presenter()
    presenter.start()

    # when
    presenter._instance_count_field.value = 13

    # then
    self.assertEqual(13, self._model.instance_count)
    self.assertEqual('Est. Cost per Hour: 130',
                     presenter._estimated_cost_label.text)

  def test_should_display_error_when_exception_raised_when_changing_instance_count(
      self):
    # given
    class _ZyncApiMock(ZyncApiMock):

      def estimated_cost(self, instance_type_label, renderer_type,
                         instance_count):
        raise ValueError('Invalid estimated cost')

    presenter = self._create_presenter(zync_api=_ZyncApiMock())

    # when
    presenter.start()

    # then
    self.assertEqual('Invalid estimated cost',
                     presenter.gui_utils.last_error_message)

  def test_should_correctly_update_estimated_cost_and_instance_type_in_model(
      self):
    # given
    class _ZyncApiMock(ZyncApiMock):

      def estimated_cost(self, instance_type_label, renderer_type,
                         instance_count):
        cost = 1
        if instance_type_label == 'scanline_3dsmax_2':
          cost = 100
        return str(cost)

    presenter = self._create_presenter(zync_api=_ZyncApiMock())
    presenter.start()
    initial_estimated_cost = presenter._estimated_cost_label.text

    # when
    presenter._instance_types_combo.selected_element = 'scanline_3dsmax_2'

    # then
    self.assertEqual('scanline_3dsmax_2', self._model.instance_type_label)
    self.assertEqual('scanline_3dsmax_2_scanline', self._model.instance_type)
    self.assertEqual('Est. Cost per Hour: 1', initial_estimated_cost)
    self.assertEqual('Est. Cost per Hour: 100',
                     presenter._estimated_cost_label.text)

  def test_should_show_error_when_exception_raise_when_changing_instance_type(
      self):
    # given
    class _ZyncApiMock(ZyncApiMock):

      def instance_type(self, instance_type_label, renderer_type):
        raise ValueError('Invalid instance type')

    presenter = self._create_presenter(zync_api=_ZyncApiMock())

    # when
    presenter.start()

    # then
    self.assertEqual('Invalid instance type',
                     presenter.gui_utils.last_error_message)

  def test_should_enable_select_files_button_when_sync_extra_assets_checked(
      self):
    # given
    presenter = self._create_presenter()
    presenter.start()
    initial_select_files_enabled = presenter._select_files_button.enabled

    # when
    presenter._sync_extra_assets_checkbox.checked = True

    # then
    self.assertFalse(initial_select_files_enabled)
    self.assertTrue(presenter._select_files_button.enabled)

  def test_should_disable_select_files_button_when_sync_extra_assets_unchecked(
      self):
    # given
    presenter = self._create_presenter()
    presenter.start()
    presenter._sync_extra_assets_checkbox.checked = True
    initial_select_files_enabled = presenter._select_files_button.enabled

    # when
    presenter._sync_extra_assets_checkbox.checked = False

    # then
    self.assertTrue(initial_select_files_enabled)
    self.assertFalse(presenter._select_files_button.enabled)

  def test_should_disable_upload_unrelated_widgets_when_upload_only_checked(
      self):
    # given
    presenter = self._create_presenter()
    presenter.start()

    # when
    presenter._upload_only_checkbox.checked = True

    # then
    for widget in self._widgets_not_used_in_upload_only(presenter):
      self.assertFalse(widget.enabled)

  def test_should_reenable_upload_unrelated_widgets_when_upload_only_unchecked(
      self):
    # given
    presenter = self._create_presenter()
    presenter.start()
    presenter._upload_only_checkbox.checked = True

    # when
    presenter._upload_only_checkbox.checked = False

    # then
    for widget in self._widgets_not_used_in_upload_only(presenter):
      self.assertTrue(widget.enabled)

  def _widgets_not_used_in_upload_only(self, presenter):
    return [
        presenter._instance_types_combo, presenter._instance_count_field,
        presenter._estimated_cost_label, presenter._priority_field,
        presenter._output_name_field, presenter._frame_range_field,
        presenter._frame_step_field, presenter._chunk_size_field,
        presenter._camera_names_combo, presenter._x_resolution_field,
        presenter._y_resolution_field
    ]

  def test_should_show_dialog_when_select_files_clicked(self):
    # given
    presenter = self._create_presenter()
    presenter.start()
    presenter._sync_extra_assets_checkbox.checked = True

    # when
    presenter._select_files_button.click()

    # then
    self.assertTrue('test_user' in self._zync_api.selected_files)
    self.assertEqual(['test_user_0.png', 'test_user_1.png', 'test_user_2.png'],
                     self._zync_api.selected_files['test_user'])

  def test_should_submit_correct_data_when_submit_clicked(self):
    # given
    expected_params = {
        'camera': 'Camera2',
        'chunk_size': 4,
        'distributed': 0,
        'frange': '1-23',
        'instance_type': 'scanline_3dsmax_2_scanline',
        'notify_complete': 1,
        'num_instances': 7,
        'output_name': 'C:/test_output.exr',
        'plugin_version': '1.2.3',
        'priority': 150,
        'proj_name': 'test_project',
        'renderer': 'scanline',
        'scene_info': {
            'max_version': '2018.4',
            'project_path': 'C:/Project/Path',
            'references': [
                'C:/asset1.png', 'C:/Path/asset2.abc', 'test_project_0.png',
                'test_project_1.png', 'test_project_2.png'
            ],
            'xrefs': ['C:/xref1.max', 'C:/xref2.max']
        },
        'step': 3,
        'sync_extra_assets': True,
        'upload_only': 0,
        'xres': 640,
        'yres': 480,
    }
    presenter = self._create_presenter()
    presenter.start()
    presenter._camera_names_combo.selected_element = 'Camera2'
    presenter._chunk_size_field.value = 4
    presenter._frame_range_field.text = '1-23'
    presenter._frame_step_field.value = 3
    presenter._instance_count_field.value = 7
    presenter._instance_types_combo.selected_element = 'scanline_3dsmax_2'
    presenter._output_name_field.text = 'C:\\test_output.exr'
    presenter._priority_field.value = 150
    presenter._new_project_checkbox.checked = True
    presenter._new_project_name_field.text = 'test_project'
    presenter._notify_complete_checkbox.checked = True
    presenter._x_resolution_field.value = 640
    presenter._y_resolution_field.value = 480
    presenter._sync_extra_assets_checkbox.checked = True
    presenter._select_files_button.click()

    # when
    presenter._submit_button.click()

    # then
    scene_file, params, job_type = self._zync_api.submitted_arguments
    self.assertEqual('C:/test_scene.max', scene_file)
    self.assertEqual(expected_params, params)
    self.assertEqual('3dsmax', job_type)
