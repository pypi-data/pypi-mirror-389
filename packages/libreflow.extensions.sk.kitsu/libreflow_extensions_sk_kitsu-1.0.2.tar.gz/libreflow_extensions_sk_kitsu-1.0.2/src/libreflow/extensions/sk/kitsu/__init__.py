import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import gazu
from kabaret import flow
from libreflow.baseflow.file import TrackedFile
from libreflow.baseflow.film import Film
from libreflow.flows.default.flow.shot import CreateKitsuShots, Sequence


class SKCreateKitsuShots(CreateKitsuShots):
    """Add digits to shots when creating shots."""

    def __init__(self, parent, name):
        """Initialize based on CreateKitsuShots."""
        super(SKCreateKitsuShots, self).__init__(parent, name)

    def add_shot_digit(self, name):
        """Add digit into shot code.

        Args:
            name (str): name of the shot (p000)

        """
        if not self._sequence.shots[name].code.get():
            shot_digit = name.replace("p", "")
            self._sequence.shots[name].code.set(shot_digit)

    def run(self, button):
        """Execute the render action.

        Args:
            button (str): The label of the button pressed by the user (e.g., 'Create Shots' or 'Cancel').

        Returns:
            Any: the result of the parent run method if executed, or None if canceled.

        """
        if button == "Cancel":
            return

        session = self.root().session()

        project_type = self.root().project().kitsu_config().project_type.get()

        skip_existing = self.skip_existing.get()
        shots_data = (
            self.root()
            .project()
            .kitsu_api()
            .get_shots_data(
                self._sequence.name(),
                episode_name=self._film.name() if project_type == "tvshow" else None,
            )
        )
        for data in shots_data:
            name = data["name"]

            if not self._sequence.shots.has_mapped_name(name):
                session.log_info(f"[Create Kitsu Shots] Creating Shot {name}")
                s = self._sequence.shots.add(name)
                self.add_shot_digit(name)
            elif not skip_existing:
                s = self._sequence.shots[name]
                session.log_info(f"[Create Kitsu Shots] Updating Default Tasks {name}")
                s.ensure_tasks()
                self.add_shot_digit(name)
            else:
                self.add_shot_digit(name)
                continue

            if self.create_task_default_files.get():
                for t in s.tasks.mapped_items():
                    session.log_info(
                        f"[Create Kitsu Shots] Updating Default Files {name} {t.name()}"
                    )
                    t.create_dft_files.files.update()
                    t.create_dft_files.run(None)
                self.add_shot_digit(name)

        self._sequence.shots.touch()


class SanityCheckFrameCountKitsu(flow.Action):
    ICON = ("icons.libreflow", "kitsu")

    _file = flow.Parent()
    _task = flow.Parent(3)
    _shot = flow.Parent(5)
    _sequence = flow.Parent(7)

    def __init__(self, parent, name):
        super(SanityCheckFrameCountKitsu, self).__init__(parent, name)
        self.start_from_batch = False
        self._kitsu_entity = None
        self.tasks_to_check = ["Storyboard", "Posing", "Anim_Rough"]
        self.files = {}
        self.animatic_file = ""
        self.warning_message = ""
        self.temp_dir = ""

    def allow_context(self, context):
        user = self.root().project().get_user()
        return user.status.get() == "Admin"

    def download_playblast(self):
        kitsu_api = self.root().project().kitsu_api()

        sequence_data = kitsu_api.get_sequence_data(self._sequence.name())
        shot_data = kitsu_api.get_shot_data(self._shot.name(), sequence_data)

        self.temp_dir = Path(tempfile.mkdtemp())
        source_dir_path = self.temp_dir / self._sequence.name()
        source_dir_path.mkdir(parents=True, exist_ok=True)

        if shot_data:
            tasks = gazu.shot.all_previews_for_shot(shot_data)

            for task in tasks:
                preview_data = tasks[task][0]
                task_data = gazu.task.get_task(preview_data["task_id"])
                task_name = task_data["task_type"]["name"]
                if task_name in self.tasks_to_check:
                    preview_file = gazu.files.get_preview_file(preview_data["id"])
                    file_name = (
                        f"{preview_file['original_name']}.{preview_file['extension']}"
                    )

                    if task_name == "Storyboard":
                        self.animatic_file = source_dir_path / file_name
                    file_path = source_dir_path / file_name

                    self.files[task_name] = file_path
                    gazu.files.download_preview_file(preview_file, file_path)

            self.root().session().log_info("Files downloaded !")


    def get_frames_count(self, file):
        check_frame = subprocess.check_output(
            f'ffprobe -v quiet -show_streams -select_streams v:0 -of json "{file}"',
            shell=True,
        ).decode()
        fields = json.loads(check_frame)["streams"][0]
        return int(fields["nb_frames"])

    def check_frames_count(self):
        if not self.animatic_file or not self.files:
            return None

        animatic_frames = self.get_frames_count(self.animatic_file)
        warning_text = (
            f"REFERENCE: Storyboard - {self.animatic_file.name}  - {animatic_frames}\n"
        )
        text = ""
        for task, file in self.files.items():
            if self.animatic_file == file:
                continue

            file_frames = self.get_frames_count(file)

            if file_frames != animatic_frames:
                text += f"\t{task} - {file.name} - {file_frames}\n"
        if text:
            warning_text = warning_text + text
            return warning_text
        return None

    def run(self, button):
        self.download_playblast()

        self.warning_message = self.check_frames_count()

        if self.warning_message:
            if self.start_from_batch is False:
                self.root().session().log_warning(
                    f"Plan has a bad frame count :\n{self.warning_message}"
                )
            self.start_from_batch = False
            shutil.rmtree(self.temp_dir)
            return True

        self.start_from_batch = False
        shutil.rmtree(self.temp_dir)
        return False


class SanityCheckFrameCountKitsuBatch(flow.Action):
    _film = flow.Parent()

    def allow_context(self, context):
        user = self.root().project().get_user()
        return user.status.get() == "Admin"

    def save_text(self, text):
        desktop_path = os.path.join(os.path.join(os.environ["USERPROFILE"]), "Desktop")
        text_file = "sanity_check_frame_count.txt"
        file_path = os.path.join(desktop_path, text_file)
        with open(file_path, "w") as file:
            file.write(text)

        self.root().session().log_info(
            f"List of files with bad frame count is save here : {file_path}"
        )

    def run(self, button):
        print_seq = False
        print_shot = False

        file_count = 0
        shot_count = 0

        text_to_save = ""

        for seq in self._film.sequences.mapped_items():
            print_seq = False
            self.root().session().log_info(seq.name())
            for shot in seq.shots.mapped_items():
                print_shot = False
                self.root().session().log_info(shot.name())
                for task in shot.tasks.mapped_items():
                    if task.name() == "posing":
                        for file in task.files.mapped_items():
                            if "tvpp" in file.name():
                                file.check_frame_count.start_from_batch = True
                                status = file.check_frame_count.run("run")
                                if status:
                                    if print_seq is False:
                                        text_to_save += f"- {seq.name()}\n"
                                        print_seq = True
                                    if print_shot is False:
                                        text_to_save += f"    - {shot.name()}\n"
                                        shot_count += 1
                                        print_shot = True
                                    text_to_save += f"        - {file.check_frame_count.warning_message}\n"

                                    file_count += 1

        text_to_save += f"Files affected: {file_count}\n"
        text_to_save += f"Shots affected: {shot_count}\n"

        if text_to_save:
            self.save_text(text_to_save)


def sanity_check_frame_count_kitsu_batch(parent):
    if isinstance(parent, Film):
        r = flow.Child(SanityCheckFrameCountKitsuBatch)
        r.name = "sanity_check_frame_count_kitsu_batch"
        r.index = None
        return r

def sanity_check_frame_count_kitsu(parent):
    if isinstance(parent, TrackedFile) and (parent.name().endswith("_tvpp")):
        r = flow.Child(SanityCheckFrameCountKitsu)
        r.name = "check_frame_count"
        r.index = None
        return r
    return None


def sk_create_kitsu_shots(parent):
    if isinstance(parent, Sequence):
        r = flow.Child(SKCreateKitsuShots)
        r.name = "create_shots"
        r.index = 25
        return r
    return None


def install_extensions(session):
    return {
        "sk": [
            sk_create_kitsu_shots,
            sanity_check_frame_count_kitsu,
            sanity_check_frame_count_kitsu_batch,
        ]
    }


from . import _version

__version__ = _version.get_versions()["version"]
