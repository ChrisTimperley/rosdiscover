from roswire import ROSVersion

from ..interpreter import model, NodeContext



@model('gazebo_ros', 'gzserver')
def gzserver(c: NodeContext):
    if c.app.description.distribution.ros == ROSVersion.ROS1:
        gzserver_ros1(c)
    else:
        gzserver_ros2(c)


def gzserver_ros2(c):
    c.read('~publish_rate', 10.0)
    c.read('~use_sim_time', True)

    c.sub('/clock', 'rosgraph_msgs/Clock')

    c.pub('/clock', 'rosgraph_msgs/Clock')

    c.provide('/pause_physics', 'std_srvs/srv/Empty')
    c.provide('/reset_simulation', 'std_srvs/srv/Empty')
    c.provide('/reset_world', 'std_srvs/srv/Empty')
    c.provide('/unpause_physics', 'std_srvs/srv/Empty')


def gzserver_ros1(c: NodeContext):
    c.pub('/clock', 'rosgraph_msgs/Clock')
    c.pub('~factory', 'gazebo_msgs/Factory')
    c.pub('~factory/light', 'gazebo_msgs/Light')
    c.pub('~light/modify', 'gazebo_msgs/Light')
    c.pub('~request', 'gazebo_msgs/Request')
    c.pub('~link_states', 'gazebo_msgs/LinkState')
    c.pub('~model_states', 'gazebo_msgs/ModelStates')

    c.sub('~response', 'gazebo_msgs/Response')
    c.sub('~set_link_state', 'gazebo_msgs/LinkState')
    c.sub('~set_model_state', 'gazebo_msgs/ModelState')

    c.provide('~spawn_sdf_model', 'gazebo_msgs/SpawnModel')
    c.provide('~spawn_urdf_model', 'gazebo_msgs/SpawnModel')
    c.provide('~delete_model', 'gazebo_msgs/DeleteModel')
    c.provide('~delete_light', 'gazebo_msgs/DeleteLight')
    c.provide('~get_model_properties', 'gazebo_msgs/GetModelProperties')
    c.provide('~get_model_state', 'gazebo_msgs/GetModelState')
    c.provide('~get_world_properties', 'gazebo_msgs/GetWorldProperties')
    c.provide('~get_joint_properties', 'gazebo_msgs/GetJointProperties')
    c.provide('~get_link_properties', 'gazebo_msgs/GetLinkProperties')
    c.provide('~get_link_state', 'gazebo_msgs/GetLinkState')
    c.provide('~get_light_properties', 'gazebo_msgs/GetLightProperties')
    c.provide('~set_light_properties', 'gazebo_msgs/SetLightProperties')
    c.provide('~get_physics_properties', 'gazebo_msgs/GetPhysicsProperties')
    c.provide('~set_link_properties', 'gazebo_msgs/SetLinkProperties')
    c.provide('~set_physics_properties', 'gazebo_msgs/SetPhysicsProperties')
    c.provide('~set_model_state', 'gazebo_msgs/SetModelState')
    c.provide('~set_model_configuration', 'gazebo_msgs/SetModelConfiguration')
    c.provide('~set_joint_properties', 'gazebo_msgs/SetJointProperties')
    c.provide('~unpause_physics', 'std_srvs/Empty')
    c.provide('~apply_body_wrench', 'gazebo_msgs/ApplyBodyWrench')
    c.provide('~apply_joint_effort', 'gazebo_msgs/ApplyJointEffort')
    c.provide('~clear_joint_forces', 'gazebo_msgs/JointRequest')
    c.provide('~clear_body_wrenches', 'gazebo_msgs/BodyRequest')
    c.provide('~reset_simulation', 'std_srvs/Empty')
    c.provide('~reset_world', 'std_srvs/Empty')

    c.write('~use_sim_time', True)
    c.read('~pub_clock_frequency')

    # plugin: diff_drive
    c.pub('/odom', 'nav_msgs/Odometry')
    c.pub('/cmd_vel', 'geometry_msgs/Twist')
    c.pub('/joint_states', 'sensor_msgs/JointState')
