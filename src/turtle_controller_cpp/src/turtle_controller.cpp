#include "rclcpp/rclcpp.hpp"
#include "turtlesim/msg/pose.hpp"
#include "turtlesim/srv/set_pen.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "my_robot_interfaces/srv/activate_turtle.hpp"

/*
   Tinc que saber explicar que fa realment el using namespace, ::, el SharedPtr del rclcpp i els placeholders
    namespace agrupa funcionalitats, variables funcions, etc, aleshores
    si poses un using namespace vols dir que totes les funcionalitats que estan en el teu codic 
    venen de ixe namespace, venen de ixe grup, el fet d'utilitzar un using namespace fa que un 
    programa coste mes de compilar

    :: es el scope resolution operator, servir per a dir quin espai de noms, 
    classe o estructura estas agafant alguna cosa

    SharedPtr de rclcpp del std::shared_ptr, es un punter inteligent,
    te ahorres fer el delete basicament
*/

using Pose = turtlesim::msg::Pose;
using Cmd_Vel = geometry_msgs::msg::Twist;
using Pen = turtlesim::srv::SetPen;
using ActivateTurtle= my_robot_interfaces::srv::ActivateTurtle;

using namespace std::placeholders;
using namespace std::chrono_literals;

class TurtleControllerNode : public rclcpp::Node
{
public:
   TurtleControllerNode() : Node("turtleSimAli"), pose(0.0), activado(true), turtle_velocity(2.0)
   {
        this->declare_parameter<std::vector<int64_t>>("color1", {255, 0, 0});
        this->declare_parameter<std::vector<int64_t>>("color2", {0, 255, 0});
        this->declare_parameter("turtle_velocity", 1.0);

        color1 = this->get_parameter("color1").as_integer_array();
        color2 = this->get_parameter("color2").as_integer_array();
        turtle_velocity = this->get_parameter("turtle_velocity").as_double();

        turtle_pose = this->create_subscription<Pose>("turtle1/pose", 10, 
         std::bind(&TurtleControllerNode::PoseCallback, this, _1)); // ue fet a ma, q gilipolles soc
      
        turtle_cmd_vel = this->create_publisher<Cmd_Vel>("turtle1/cmd_vel", 10);

        turtle_pen = this->create_client<Pen>("turtle1/set_pen");

        turtle_service = this->create_service<ActivateTurtle>(
            "activate_turtle", std::bind(&TurtleControllerNode::callbackActivateTurtle, this, _1, _2));
        RCLCPP_INFO(this->get_logger(), "TurtleControllerNode has been started.");

        param_handle = this->add_post_set_parameters_callback(
            std::bind(&TurtleControllerNode::parametersCallback, this, _1)
        );
   }

   void PoseCallback(const Pose::SharedPtr pose) 
   {
      
      if(this->activado)
      {
         auto vel = Cmd_Vel();
         if(pose->x >= 5.5)
         {
            vel.linear.x = turtle_velocity * 2.0;
            vel.angular.z = turtle_velocity * 2.0;
         }
         else
         {
            vel.linear.x = turtle_velocity;
            vel.angular.z = turtle_velocity;
         }

         if(pose->x >= 5.5 && this->pose < 5.5)
         {
            this->pose = pose->x;
            RCLCPP_INFO(get_logger(), "Cambiant de color");
            penService(color1[0], color1[1], color1[2]);
         }
         else if(pose->x < 5.5 && this->pose > 5.5)
         {
            this->pose = pose->x;
            RCLCPP_INFO(get_logger(), "Cambiant de color");
            penService(color2[0], color2[1], color2[2]);
         }
         this->turtle_cmd_vel->publish(vel); // publicant directament en el subscriber callback
      }

   }

    void parametersCallback(const std::vector<rclcpp::Parameter> & parameters)
    {
        for(const auto &param: parameters)
        {
            if(param.get_name() == "color1")
            {
                color1 = param.as_integer_array();
            }
            else if(param.get_name() == "color2")
            {
                color2 = param.as_integer_array();
            }
            else if(param.get_name() == "turtle_velocity")
            {
                turtle_velocity = param.as_double();
            }
        }
    }

   void penService(int r, int g , int b)
   {
      while (!turtle_pen->wait_for_service(1s)) 
      {
         RCLCPP_WARN(this->get_logger(), "Waiting for the server...");
      }
      
      auto request = std::make_shared<Pen::Request>();
      request->r = r;
      request->g = g;
      request->b = b;

      turtle_pen->async_send_request(
         request, std::bind(&TurtleControllerNode::callbackSetPenResponse, this, _1));
   }
private:

   void callbackSetPenResponse(rclcpp::Client<Pen>::SharedFuture future)
   {
      auto response = future.get();
      RCLCPP_INFO(this->get_logger(), "Servicio cumplido\n");
   }

   void callbackActivateTurtle(const ActivateTurtle::Request::SharedPtr request, const ActivateTurtle::Response::SharedPtr response)
   {
      if (request->activate)
      {
         RCLCPP_INFO(this->get_logger(), "La tortuga esta activada xe");
         response->message = "Eres un puto, com fas que la tortuga vaja tan rapit";
         this->activado = true;
      }
      else if (!request->activate)
      {
         RCLCPP_INFO(this->get_logger(), "La tortuga NO esta activada xe");
         response->message = "Gayyyy";
         this->activado = false;
      }
   }

   rclcpp::Subscription<Pose>::SharedPtr turtle_pose;
   rclcpp::Publisher<Cmd_Vel>::SharedPtr turtle_cmd_vel;
   rclcpp::Client<Pen>::SharedPtr turtle_pen;
   rclcpp::Service<ActivateTurtle>::SharedPtr turtle_service;

   float pose;
   bool activado;

   std::vector<int64_t> color1;
   std::vector<int64_t> color2;

   double turtle_velocity;

    PostSetParametersCallbackHandle::SharedPtr param_handle;

};

/*
TMUX: 
Ctrl+b % -> dividir verticalmente
Ctrl+b " -> dividir horizontalmente
*/

int main(int argc, char **argv)
{
   rclcpp::init(argc, argv);
   auto node = std::make_shared<TurtleControllerNode>();
   rclcpp::spin(node);
   rclcpp::shutdown();
   return 0;
}

/*
resum:

To write a service server, you must do the following:
1. As the name and interface are defined by the server, you have to choose them here. 
As a best practice, use a verb as the first word in the name.
2. Import the interface in your code and create the service server in the constructor.
3. Add a callback method to process any received request.
When choosing a service interface, if you can’t find an existing one that perfectly matches what you
need, then you have to create and build your own. To do that, you must do the following:
1. Create and set up a package dedicated to interfaces. If you already have one for your application, use it.
2. Add the new service interface to the package and build it.3. Now, you can use this interface in your service server.
To write a service client, do the following:
1. If you’re writing a client, it means that there is an existing server on the other side.
 Find which name and interface you need to use.
2. Import the interface into your code and create the service client in the constructor.
3. Create a method to call the service. In this method, you send the request asynchronously,
 and then register a callback to process the response.
4. You can call the service from anywhere in your code.

*/