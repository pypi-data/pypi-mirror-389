from dedal.configuration.SpackConfig import SpackConfig
from dedal.model.SpackDescriptor import SpackDescriptor
from dedal.spack_factory.SpackOperation import SpackOperation
from dedal.spack_factory.SpackOperationCreator import SpackOperationCreator


def test_serialize_and_deserialize_spack_operation(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('test_spack_env', install_dir)
    config = SpackConfig(env=env, install_dir=install_dir, serialize_name='data_test.pkl')
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    spack_operation.serialize()
    loaded_spack_operation: SpackOperation = SpackOperation.deserialize(install_dir, "data_test.pkl")
    assert isinstance(loaded_spack_operation, SpackOperation)
    assert loaded_spack_operation.spack_config.env.name == spack_operation.spack_config.env.name
