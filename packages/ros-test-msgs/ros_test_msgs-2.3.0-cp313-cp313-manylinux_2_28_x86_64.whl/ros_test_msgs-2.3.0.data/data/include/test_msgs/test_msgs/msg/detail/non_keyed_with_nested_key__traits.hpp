// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from test_msgs:msg/NonKeyedWithNestedKey.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "test_msgs/msg/non_keyed_with_nested_key.hpp"


#ifndef TEST_MSGS__MSG__DETAIL__NON_KEYED_WITH_NESTED_KEY__TRAITS_HPP_
#define TEST_MSGS__MSG__DETAIL__NON_KEYED_WITH_NESTED_KEY__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "test_msgs/msg/detail/non_keyed_with_nested_key__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'nested_data'
#include "test_msgs/msg/detail/keyed_string__traits.hpp"

namespace test_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const NonKeyedWithNestedKey & msg,
  std::ostream & out)
{
  out << "{";
  // member: nested_data
  {
    out << "nested_data: ";
    to_flow_style_yaml(msg.nested_data, out);
    out << ", ";
  }

  // member: some_int
  {
    out << "some_int: ";
    rosidl_generator_traits::value_to_yaml(msg.some_int, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const NonKeyedWithNestedKey & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: nested_data
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "nested_data:\n";
    to_block_style_yaml(msg.nested_data, out, indentation + 2);
  }

  // member: some_int
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "some_int: ";
    rosidl_generator_traits::value_to_yaml(msg.some_int, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const NonKeyedWithNestedKey & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace test_msgs

namespace rosidl_generator_traits
{

[[deprecated("use test_msgs::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const test_msgs::msg::NonKeyedWithNestedKey & msg,
  std::ostream & out, size_t indentation = 0)
{
  test_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use test_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const test_msgs::msg::NonKeyedWithNestedKey & msg)
{
  return test_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<test_msgs::msg::NonKeyedWithNestedKey>()
{
  return "test_msgs::msg::NonKeyedWithNestedKey";
}

template<>
inline const char * name<test_msgs::msg::NonKeyedWithNestedKey>()
{
  return "test_msgs/msg/NonKeyedWithNestedKey";
}

template<>
struct has_fixed_size<test_msgs::msg::NonKeyedWithNestedKey>
  : std::integral_constant<bool, has_fixed_size<test_msgs::msg::KeyedString>::value> {};

template<>
struct has_bounded_size<test_msgs::msg::NonKeyedWithNestedKey>
  : std::integral_constant<bool, has_bounded_size<test_msgs::msg::KeyedString>::value> {};

template<>
struct is_message<test_msgs::msg::NonKeyedWithNestedKey>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // TEST_MSGS__MSG__DETAIL__NON_KEYED_WITH_NESTED_KEY__TRAITS_HPP_
