#include "rclcpp/rclcpp.hpp"
#include "example_interfaces/msg/int64.hpp"

using namespace std::placeholders;

class NumberPublisherNode : public rclcpp::Node
{
public:
    NumberPublisherNode() : Node("number_publisher")
    {
        this->declare_parameter("number", 2);
        this->declare_parameter("period_timer", 1.0);

        number = this->get_parameter("number").as_int();
        timer = this->get_parameter("period_timer").as_double();

        number_publisher_ = this->create_publisher<example_interfaces::msg::Int64>("number", 10);
        number_timer_ = this->create_wall_timer(std::chrono::duration<double>(timer), std::bind(&NumberPublisherNode::publishNumber, this));
        RCLCPP_INFO(this->get_logger(), "Number publisher has been started.");

        param_handle = this->add_post_set_parameters_callback(
            std::bind(&NumberPublisherNode::parametersCallback, this, _1)
        );

    }

    void parametersCallback(const std::vector<rclcpp::Parameter> & parameters)
    {
        for(const auto &param: parameters)
        {
            if(param.get_name() == "number")
            {
                number = param.as_int();
            }
        }
    }

private:
    void publishNumber()
    {
        auto msg = example_interfaces::msg::Int64();
        msg.data = number;
        number_publisher_->publish(msg);
    }

    int number;
    double timer;

    PostSetParametersCallbackHandle::SharedPtr param_handle;

    rclcpp::Publisher<example_interfaces::msg::Int64>::SharedPtr number_publisher_;
    rclcpp::TimerBase::SharedPtr number_timer_;

};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<NumberPublisherNode>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}