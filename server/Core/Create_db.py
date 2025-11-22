from DB.Models.Cell import Cell #------------------------------------------------------------------------1
from DB.Models.CellHasDevice import CellHasDevice #------------------------------------------------------2
from DB.Models.Command import Command #------------------------------------------------------------------3
from DB.Models.Consumption import Consumption #----------------------------------------------------------4
from DB.Models.Device import Device #--------------------------------------------------------------------5
from DB.Models.Drop import Drop #------------------------------------------------------------------------6
from DB.Models.DropOperations import DropOperations #----------------------------------------------------7
from DB.Models.DropOperationsHasDevice import DropOperationsHasDevice #----------------------------------8
from DB.Models.Error import Error #----------------------------------------------------------------------9
from DB.Models.ErrorHasDevice import ErrorHasDevice #---------------------------------------------------10
from DB.Models.Group import Group #---------------------------------------------------------------------11
from DB.Models.Help import Help #-----------------------------------------------------------------------12
from DB.Models.History import History #-----------------------------------------------------------------13
from DB.Models.Identification import Identification #---------------------------------------------------14
from DB.Models.Load import Load #-----------------------------------------------------------------------15
from DB.Models.LoadOperations import LoadOperations #---------------------------------------------------16
from DB.Models.LoadOperationsHasDevice import LoadOperationsHasDevice #---------------------------------17
from DB.Models.MassDrop import MassDrop #---------------------------------------------------------------18
from DB.Models.MassLoad import MassLoad #---------------------------------------------------------------19
from DB.Models.MassDropHasDevice import MassDropHasDevice #---------------------------------------------20
from DB.Models.MassLoadHasDevice import MassLoadHasDevice #---------------------------------------------21
from DB.Models.OperationsConsumption import OperationsConsumption #-------------------------------------22
from DB.Models.OperationsConsumptionHasDevice import OperationsConsumptionHasDevice #-------------------23
from DB.Models.Page import Page
from DB.Models.Plan import Plan #-----------------------------------------------------------------------24
from DB.Models.ActualNorm import ActualNorm #-----------------------------------------------------------25
from DB.Models.ActualNormHasDevice import ActualNormHasDevice #-----------------------------------------26
from DB.Models.Rights import Rights #-------------------------------------------------------------------27
from DB.Models.Role import Role #-----------------------------------------------------------------------28
from DB.Models.Status import Status #-------------------------------------------------------------------29
from DB.Models.ToolLocation import ToolLocation #-------------------------------------------------------30
from DB.Models.ToolTypes import ToolTypes
from DB.Models.Tools import Tools #---------------------------------------------------------------------31
from DB.Models.ToolsHasDevice import ToolsHasDevice #---------------------------------------------------32
from DB.Models.ToolsNorm import ToolsNorm #---------------------------------------------------------------33
from DB.Models.Type import Type #-----------------------------------------------------------------------34
from DB.Models.User import User #-----------------------------------------------------------------------35
from DB.Models.Settings import Settings  #--------------------------------------------------------------36
from DB.Models.DeviceDefaults import DeviceDefaults  #--------------------------------------------------37

from sqlalchemy import create_engine
from DB.Data.base import Base
import os

from options import db_path


# from config import db_path


def rebuild_db():
    # modules = [Help, Error, Role, Plan, Group, Rights, MassDrop, MassLoad, Status, User, Identification, Tools, Cell,
    #            Load, Drop, Consumption, History, DropOperations, OperationsConsumption, LoadOperations]
    # modules = [Cell, Error, Group, Help, History, Identification, Plan, Rights, Role, Tools, User, MassLoad, MassDrop,
    #            LoadOperations, OperationsConsumption, Drop, Status, Load, DropOperations, Consumption]
    modules = [
        Cell, CellHasDevice, Command, Consumption, Device, Drop, DropOperations, DropOperationsHasDevice,
        Error, ErrorHasDevice, Group, Help, History, Identification, Load, LoadOperations,
        LoadOperationsHasDevice, MassDrop, MassLoad, MassDropHasDevice, MassLoadHasDevice,
        OperationsConsumption, OperationsConsumptionHasDevice, Plan, ActualNorm, ActualNormHasDevice, Rights,
        Role, Status, ToolTypes, ToolLocation, Tools, ToolsHasDevice, ToolsNorm, Type, User, Page,
        Settings, DeviceDefaults
    ]
    # Получаем текущую директорию
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent = os.path.dirname(current_dir)

    # Определяем путь к родительской директории  os.path.dirname()
    parent_dir = parent + "\\"  + "DB" + "\\" + "Data"
    # Формируем полный путь к базе данных в родительской директории
    db_filename = os.path.join(parent_dir, db_path)

    # Определите имя файла, который хотите удалить
    # Проверьте, существует ли файл
    if os.path.exists(db_filename):
        try:
            os.remove(db_filename)
            print(f"Файл '{db_filename}' был успешно удален.")
        except Exception as e:
            print(f"Ошибка при удалении файла: {e}")
    else:
         print(f"Файл '{db_filename}' не найден.")

    # Включение логирования SQLAlchemy
    # logging.basicConfig()
    # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    # Создаем движок базы данных с использованием относительного пути
    # engine = create_engine(f'sqlite:///{db_path}')
    # Создаем файл и записываем в него пример данных

    try:

        with open(db_filename, 'w') as file:
            # Вы можете записывать строки в файл, используя метод write(), echo=True
            file.write('')
        print(f"Файл '{db_filename}' был успешно создан.")
    except Exception as e:
        print(f"Ошибка при создании файла: {e}")
        return
    # Создание базы данных и таблиц
    engine = create_engine(f'sqlite:///{db_filename}')
    print(Base.metadata.tables.keys())
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)  # Создает все таблицы, описанные в Base


if __name__ == "__main__":
    rebuild_db()
