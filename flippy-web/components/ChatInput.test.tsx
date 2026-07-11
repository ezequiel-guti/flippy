import { render, screen, fireEvent } from "@testing-library/react";
import ChatInput from "./ChatInput";

describe("ChatInput", () => {
  it("calls onSend with the typed text and clears the input", () => {
    const onSend = jest.fn();
    render(<ChatInput onSend={onSend} />);

    const input = screen.getByLabelText(/escribí tu consulta/i);
    fireEvent.change(input, { target: { value: "Hola" } });
    fireEvent.click(screen.getByText("Enviar"));

    expect(onSend).toHaveBeenCalledWith("Hola", null);
    expect(input).toHaveValue("");
  });

  it("disables the send button when there is no text or image", () => {
    render(<ChatInput onSend={jest.fn()} />);
    expect(screen.getByText("Enviar")).toBeDisabled();
  });

  it("disables inputs when disabled prop is true", () => {
    render(<ChatInput onSend={jest.fn()} disabled />);
    expect(screen.getByLabelText(/escribí tu consulta/i)).toBeDisabled();
    expect(screen.getByLabelText("Adjuntar imagen")).toBeDisabled();
  });
});
