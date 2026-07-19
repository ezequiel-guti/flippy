import { render, screen, fireEvent } from "@testing-library/react";
import IOSInstallBanner from "./IOSInstallBanner";

function setUserAgent(ua: string) {
  Object.defineProperty(window.navigator, "userAgent", { value: ua, configurable: true });
}

function setStandalone(value: boolean | undefined) {
  Object.defineProperty(window.navigator, "standalone", { value, configurable: true });
}

function mockMatchMedia(matches: boolean) {
  window.matchMedia = jest.fn().mockImplementation((query: string) => ({
    matches,
    media: query,
    addListener: jest.fn(),
    removeListener: jest.fn(),
  })) as unknown as typeof window.matchMedia;
}

const IOS_SAFARI_UA =
  "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1";
const ANDROID_CHROME_UA =
  "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36";

describe("IOSInstallBanner", () => {
  beforeEach(() => {
    localStorage.clear();
    setStandalone(false);
    mockMatchMedia(false);
  });

  it("shows the install banner on iOS Safari when not installed", () => {
    setUserAgent(IOS_SAFARI_UA);
    render(<IOSInstallBanner />);
    expect(screen.getByText(/agregar a pantalla de inicio/i)).toBeInTheDocument();
  });

  it("does not show on non-iOS browsers", () => {
    setUserAgent(ANDROID_CHROME_UA);
    render(<IOSInstallBanner />);
    expect(screen.queryByText(/agregar a pantalla de inicio/i)).not.toBeInTheDocument();
  });

  it("does not show when already running as an installed PWA", () => {
    setUserAgent(IOS_SAFARI_UA);
    setStandalone(true);
    render(<IOSInstallBanner />);
    expect(screen.queryByText(/agregar a pantalla de inicio/i)).not.toBeInTheDocument();
  });

  it("dismisses and remembers the dismissal across renders", () => {
    setUserAgent(IOS_SAFARI_UA);
    const { unmount } = render(<IOSInstallBanner />);
    fireEvent.click(screen.getByLabelText("Cerrar aviso de instalación"));
    expect(screen.queryByText(/agregar a pantalla de inicio/i)).not.toBeInTheDocument();
    unmount();

    render(<IOSInstallBanner />);
    expect(screen.queryByText(/agregar a pantalla de inicio/i)).not.toBeInTheDocument();
  });
});
