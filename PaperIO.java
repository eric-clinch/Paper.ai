import java.awt.Color;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.KeyEventDispatcher;
import java.awt.KeyboardFocusManager;
import java.awt.event.KeyEvent;
import java.awt.image.BufferStrategy;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.net.Socket;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;

import javax.swing.JFrame;

public class PaperIO {
	
	private static class RGB {
		int r;
		int g;
		int b;
		private Color color;
		
		public RGB(int r, int g, int b) {
			this.r = r;
			this.g = g;
			this.b = b;
			this.color = new Color(r, g, b);
		}
		
		public Color getColor() {
			return color;
		}
		
		public RGB getLighterColor() {
			int redWhiteDistance = 255 - r;
			int greenWhiteDistance = 255 - g;
			int blueWhiteDistance = 255 - b;
			
			redWhiteDistance /= 2;
			greenWhiteDistance /= 2;
			blueWhiteDistance /= 2;
			
			return new RGB(255 - redWhiteDistance, 255 - greenWhiteDistance, 255 - blueWhiteDistance);
		}
		
		public RGB getAverageColor(RGB other) {
			int avgR = (r + other.r) / 2;
			int avgG = (g + other.g) / 2;
			int avgB = (b + other.b) / 2;
			return new RGB(avgR, avgG, avgB);
		}
		
		public boolean equals(RGB other) {
			return other != null && r == other.r && g == other.g && b == other.b;
		}
	}
	
	private static class Head {
		int row;
		int col;
		
		public Head(int row, int col) {
			this.row = row;
			this.col = col;
		}
	}
	
	public static class KeyController implements KeyEventDispatcher {
		
		public static void connectToServer() throws Exception {
			int port = Integer.parseInt(portStr);			
			Socket server = new Socket(host, port);
			serverOutput = new PrintStream(server.getOutputStream());
			serverInput = new BufferedReader(new InputStreamReader(server.getInputStream()));
		}

	    public boolean dispatchKeyEvent(KeyEvent e) {
	        int kc = e.getKeyCode();
	        if (e.getID() == KeyEvent.KEY_PRESSED) {
		        if (inGame) {
			            if (kc == KeyEvent.VK_UP) serverOutput.print("0");
			            else if (kc == KeyEvent.VK_DOWN) serverOutput.print("1");
			            else if (kc == KeyEvent.VK_LEFT) serverOutput.print("2");
			            else if (kc == KeyEvent.VK_RIGHT) serverOutput.print("3");
		        }
		        else {
		        	if (portStr == null) {
		        		if (kc == KeyEvent.VK_BACK_SPACE && host.length() > 0) host = host.substring(0, host.length() - 1);
		        		else if (kc == KeyEvent.VK_ENTER) portStr = ""; // the user will now start to enter the port number
		        		else host = host + e.getKeyChar();
		        	}
		        	else {
		        		if (kc == KeyEvent.VK_BACK_SPACE && portStr.length() > 0) portStr = portStr.substring(0, portStr.length() - 1);
		        		else if (kc == KeyEvent.VK_ENTER) {
		        			try {
		        				connectToServer();
		        			    Thread t = new Thread(new HandleServer());
		        			    t.start();
		        			    inGame = true;
		        			}
		        			catch (Exception exception) {
		        				System.out.println(exception);
		        				host = "";
		        				portStr = null;
		        				inGame = false;
		        			}
		        		}
		        		else portStr = portStr + e.getKeyChar();
		        	}
		        }
	        }

	        return false;
	    }
	    
	    public synchronized void init() {
	    	KeyboardFocusManager.getCurrentKeyboardFocusManager().addKeyEventDispatcher(this);
	    }
	}
	
	static int boardSize = 51;
	static int cellSize = 12;
	static int windowSize = boardSize * cellSize;
	static int[][] board = new int[boardSize][boardSize];
	static int[][] tails = new int[boardSize][boardSize];
	static RGB[][] boardRGBs = new RGB[boardSize][boardSize];
	static boolean[][] prevHeadLocations = new boolean[boardSize][boardSize];
	static ArrayList<Head> heads = new ArrayList<Head>();
	static JFrame frame;
	static BufferStrategy strategy;
	static Graphics graphics;
	static HashMap<Integer, RGB> intToRGB;
	static Color black = new Color(0, 0, 0);
	static Color white = new Color(255, 255, 255);
	static BufferedReader serverInput;
	static PrintStream serverOutput;
	static boolean inGame = false;
	static String host = "";
	static String portStr = null;
	static Semaphore boardSemaphore = new Semaphore(1);
	
	public static void initHashMap() {
		intToRGB = new HashMap<Integer, RGB>();
		intToRGB.put(-1, new RGB(169, 169, 169)); // gray
		intToRGB.put(0, new RGB(255, 255, 255)); // white
		intToRGB.put(1, new RGB(25, 25, 255)); // blue
		intToRGB.put(2, new RGB(255, 25, 25)); // red
		intToRGB.put(3, new RGB(25, 255, 25)); // green
		intToRGB.put(4, new RGB(230, 230, 0)); // yellow
		intToRGB.put(5, new RGB(255, 20, 147)); // pink
		intToRGB.put(6, new RGB(160, 32, 240)); // purple
		intToRGB.put(7, new RGB(32, 21, 11)); // brown
	}
	
	public static class DrawBoard implements Runnable {
		public void drawGetConnectionInfo() {
			Font font = new Font("TimesRoman", Font.PLAIN, 30);
			graphics.setFont(font);
			graphics.clearRect(0, 0, windowSize, windowSize);
			graphics.drawString("host: " + host, 100, 100);
			if (portStr != null) graphics.drawString("port: " + portStr, 100, 150);
		}
		
		public void drawBoard() {
			try {
				boardSemaphore.acquire();
			} catch (InterruptedException e) {
				System.out.println(e);
				return;
			}
			for (int row = 0; row < boardSize; row++) {
				for (int col = 0; col < boardSize; col++) {					
					int playerInt = board[row][col];
					int tailInt = tails[row][col];
					RGB rgb;
					if (tailInt > 0) {
						rgb = intToRGB.get(tailInt);
						rgb = rgb.getLighterColor();
						if (playerInt > 0) {
							RGB playerRGB = intToRGB.get(playerInt);
							rgb = rgb.getAverageColor(playerRGB);
						}
					}
					else {
						rgb = intToRGB.get(playerInt);
					}
					
					if (!rgb.equals(boardRGBs[row][col]) || prevHeadLocations[row][col]) {
						boardRGBs[row][col] = rgb;
						
						int yTop = row * cellSize;
						int xLeft = col * cellSize;
						Color color = rgb.getColor();
						graphics.setColor(color);
						graphics.fillRect(xLeft, yTop, cellSize, cellSize);
						prevHeadLocations[row][col] = false;
					}
				}
			}
			
			int radius = 5;
			graphics.setColor(black);
			for (Head h : heads) {
				if (h.row < 0 || h.row >= boardSize || h.col < 0 || h.col >= boardSize) continue;
				prevHeadLocations[h.row][h.col] = true;
				int dotY = h.row * cellSize + cellSize / 2 - radius / 2;
				int dotX = h.col * cellSize + cellSize / 2 - radius / 2;
				graphics.fillOval(dotX, dotY, 5, 5);
			}
			boardSemaphore.release();
		}
		
		public void run() {
			if (inGame) drawBoard();
			else drawGetConnectionInfo();
		}
	}
	
	private static class HandleServer implements Runnable {
		private void parseState(String stateStr) {
			try {
				boardSemaphore.acquire();
			} catch (InterruptedException e) {
				System.out.println(e);
				return;
			}
			String[] parts = stateStr.split("/");
			String coordinatesStr = parts[0];
			String headsStr = parts[1];
			
			String[] coordinatesStrs = coordinatesStr.split("\\.");
			for (int row = 0; row < boardSize; row++) {
				for (int col = 0; col < boardSize; col++) {
					int index = row * boardSize + col;
					String coordinateState = coordinatesStrs[index];
					String[] stateParts = coordinateState.split(",");
					board[row][col] = Integer.parseInt(stateParts[0]);
					tails[row][col] = Integer.parseInt(stateParts[1]);
				}
			}
			
			heads = new ArrayList<Head>();
			String[] headsStrs = headsStr.split("\\.");
			for (int i = 0; i < headsStrs.length; i++) {
				String[] headCoordinates = headsStrs[i].split(",");
				int row = Integer.parseInt(headCoordinates[0]);
				int col = Integer.parseInt(headCoordinates[1]);
				heads.add(new Head(row, col));
			}
			boardSemaphore.release();
		}
		
		public void run() {
			String msg;
			try{
				while ((msg = serverInput.readLine()) != null) {
					parseState(msg);
				}
			}
			catch (IOException e) {
				System.out.println(e);
			}
		}
	}
	
	public static void main(String[] args) {		
		initHashMap();
		
		frame = new JFrame();
		frame.setSize(windowSize, windowSize);
		frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		frame.setVisible(true);
		frame.createBufferStrategy(1);
		strategy = frame.getBufferStrategy();
		graphics = strategy.getDrawGraphics();
		
		KeyController k = new KeyController();
		k.init();
		
	    ScheduledExecutorService service = Executors
	                    .newSingleThreadScheduledExecutor();
	    service.scheduleAtFixedRate(new DrawBoard(), 0, 25, TimeUnit.MILLISECONDS); // redraw every 50 milliseconds
	}
}
